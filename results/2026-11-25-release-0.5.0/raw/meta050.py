import json, os
d = os.path.expanduser("~/inkling2/rig")
ENGINE = "SparkInkling 0.5.0 (Atlas, Enntity/atlas inkling2/rc-0.5.0-20261124 @ 1559aa4bc)"
IMAGE = "ghcr.io/enntity/atlas-sparkinkling:13920bc38fd6 (the release image)"
COMMON = ("verifies stop where the drafter is unsure (ATLAS_DFLASH_CONF_WIDTH=1: the engine learns while serving how often each draft "
          "confidence is accepted), drafts go off for a sequence whose steps stop paying, for 32 tokens at first and doubling while "
          "re-probes fail (ATLAS_DFLASH_ADAPTIVE=1, threshold %s accepted a block), in place of the engine throughput gate (ATLAS_MTP_GATE_FORCE=1)")
DRAFTER = {
 "strict": "DFlash2 (incoai/Inkling-2-Mini-DFlash2 @ 4f9088ea66c2), greedy drafts: 7 draft tokens with one live request, 3 each with two, plain decode from three (ATLAS_DFLASH_BATCH_DEPTH=1:7,2:3,1000000:0); " + COMMON % "1.0 (ATLAS_DFLASH_ADAPTIVE_MIN=1.0)",
 "spark": "DFlash2 (incoai/Inkling-2-Mini-DFlash2 @ 4f9088ea66c2), greedy drafts: 7 draft tokens with one live request, plain decode from two (ATLAS_DFLASH_BATCH_DEPTH=1:7,1000000:0); " + COMMON % "2.0, the engine's",
}
for mode in ("strict", "spark"):
    p = f"{d}/metadata-image-{mode}.json"
    m = json.load(open(p))
    m["serving_engine"], m["serving_image"], m["drafter"] = ENGINE, IMAGE, DRAFTER[mode]
    m["context_limit"] = 1048576
    m["kv_cache_dtype"] = "auto (bf16), window-bounded: the 40 sliding-window visits keep their last 1,024 tokens"
    m["scheduler"] = m["scheduler"].replace("--ssm-cache-slots=128", "--ssm-cache-slots=264")
    m["competing_traffic"] = "none (the voice engines suspended through LLooM for the window)"
    json.dump(m, open(p, "w"), indent=1)
    print(mode, m["serving_engine"], "|", m["serving_image"], "|", m["context_limit"], "|", m["scheduler"][:90])
