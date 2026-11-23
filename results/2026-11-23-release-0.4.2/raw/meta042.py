import json, os
d = os.path.expanduser("~/inkling2/rig")
ENGINE = "SparkInkling 0.4.2 (Atlas, Enntity/atlas inkling2/concurrent-spec-20261123 @ d3318e087)"
IMAGE = "ghcr.io/enntity/atlas-sparkinkling:b1e18bf91437 (the release image)"
DRAFTER = {
 "strict": "DSpark (bundled mtp.safetensors), greedy drafts: 7 draft tokens with one live request, 2 each with two (one shared propose pass), plain decode from three (ATLAS_DFLASH_BATCH_DEPTH=1:7,2:2,1000000:0); verifies stop where the drafter is unsure (ATLAS_DFLASH_CONF_WIDTH=1: the engine learns while serving how often each draft confidence is accepted), drafts go off for a sequence whose steps stop paying, for 32 tokens at first and doubling while re-probes fail (ATLAS_DFLASH_ADAPTIVE=1, threshold 2.0 accepted a block), in place of the engine throughput gate (ATLAS_MTP_GATE_FORCE=1)",
 "spark": "DSpark (bundled mtp.safetensors), greedy drafts: 7 draft tokens with one live request, plain decode from two (ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0); verifies stop where the drafter is unsure (ATLAS_DFLASH_CONF_WIDTH=1: the engine learns while serving how often each draft confidence is accepted), drafts go off for a sequence whose steps stop paying, for 32 tokens at first and doubling while re-probes fail (ATLAS_DFLASH_ADAPTIVE=1, threshold 2.5 (ATLAS_DFLASH_ADAPTIVE_MIN=2.5) accepted a block), in place of the engine throughput gate (ATLAS_MTP_GATE_FORCE=1)",
}
for mode in ("strict", "spark"):
    p = f"{d}/metadata-image-{mode}.json"
    m = json.load(open(p))
    m["serving_engine"], m["serving_image"], m["drafter"] = ENGINE, IMAGE, DRAFTER[mode]
    m["scheduler"] = m["scheduler"].replace("ATLAS_QWEN4EXP_AUX_PINNED=1)", "ATLAS_QWEN4EXP_AUX_PINNED=1) and branch checkpoints (ATLAS_GLM_PC_BRANCH=1, ATLAS_GLM_PC_BRANCH_MIN=512)") if "PC_BRANCH" not in m["scheduler"] else m["scheduler"]
    m["competing_traffic"] = "none (the voice engines suspended through LLooM for the window)"
    json.dump(m, open(p, "w"), indent=1)
    print(mode, m["serving_engine"], "|", m["serving_image"], "|", m["quantisation"][:60])
