"""Reference image features for Inkling 2 Mini from the transformers implementation.

usage (inside the vLLM Inkling image): python vis_ref.py MODEL_DIR IMAGE OUT.npz
Loads only the vision tower (float32), runs the checkpoint's image processor, and saves the
per-token features the language model receives (pooler_output), the grid, and the pixel patches.
"""
import json, re, sys
import numpy as np
import torch
from PIL import Image
from safetensors import safe_open
from transformers.models.inkling2.configuration_inkling2 import Inkling2VisionConfig
from transformers.models.inkling2.image_processing_inkling2 import Inkling2ImageProcessor
from transformers.models.inkling2.modeling_inkling2 import Inkling2VisionModel

model_dir, image_path, out = sys.argv[1:4]
cfg = json.load(open(f"{model_dir}/config.json"))["vision_config"]
cfg.pop("model_type", None)
vc = Inkling2VisionConfig(**cfg)
print("rope", vc.rope_parameters, "act", vc.hidden_act, "merge", vc.spatial_merge_size, "patch", vc.patch_size)
model = Inkling2VisionModel(vc).float().eval()
RENAMES = [
    (r"^model\.visual\.backbone\.embeddings\.position_embedding$", "embeddings.position_embedding.weight"),
    (r"^model\.visual\.backbone\.embeddings\.", "embeddings."),
    (r"^model\.visual\.backbone\.ln_pre\.", "pre_layernorm."),
    (r"^model\.visual\.backbone\.layers\.", "layers."),
    (r"^model\.visual\.proj_in\.", "merger.linear_1."),
    (r"^model\.visual\.proj_out\.", "merger.linear_2."),
    (r"\.ln_1\.", ".layernorm_before."), (r"\.ln_2\.", ".layernorm_after."),
    (r"\.mlp\.c_fc\.", ".mlp.fc1."), (r"\.mlp\.c_proj\.", ".mlp.fc2."),
    (r"\.ls_1\.gamma$", ".lambda_1"), (r"\.ls_2\.gamma$", ".lambda_2"),
]
state = {}
with safe_open(f"{model_dir}/model-00001-of-00001.safetensors", "pt") as f:
    for k in f.keys():
        if not k.startswith("model.visual."):
            continue
        n = k
        for a, b in RENAMES:
            n = re.sub(a, b, n)
        state[n] = f.get_tensor(k).float()
missing, unexpected = model.load_state_dict(state, strict=False)
print("missing", missing, "unexpected", unexpected)
assert not unexpected and all("inv_freq" in m for m in missing), (missing, unexpected)
proc = Inkling2ImageProcessor()
feats = proc(images=[Image.open(image_path)], return_tensors="pt")
with torch.no_grad():
    o = model(pixel_values=feats["pixel_values"], image_grid_thw=feats["image_grid_thw"])
np.savez(out, features=o.pooler_output.numpy(), grid=feats["image_grid_thw"].numpy(), pixels=feats["pixel_values"].numpy(),
         last_hidden=o.last_hidden_state.numpy())
print("grid", feats["image_grid_thw"].tolist(), "features", tuple(o.pooler_output.shape),
      "norm", float(o.pooler_output.norm(dim=-1).mean()), "first", o.pooler_output[0, :4].tolist())
