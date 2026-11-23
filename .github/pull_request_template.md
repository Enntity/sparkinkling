## What changes

## Evidence

- [ ] Checks pass (`python3 -m unittest discover -s install -p 'test_*.py'`)
- [ ] For a change to `install/` or the engine pin: `./start.sh` from a clean
      clone on a Spark, smoke test answered in the modes it touches
- [ ] For a performance claim: raw receipts and `SHA256SUMS` under `results/`,
      with the baseline measured on the same Spark and the opt-ins named

Known regressions, noise or untested boundaries:
