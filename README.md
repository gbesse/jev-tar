# jev-tar

**Technology-assisted review for legal teams: rank documents, propagate families, and produce elusion statistics and audit artifacts.**

[![Tests](https://github.com/gbesse/jev-tar/actions/workflows/test.yml/badge.svg)](https://github.com/gbesse/jev-tar/actions/workflows/test.yml) ![MIT](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![Public alpha](https://img.shields.io/badge/status-public_alpha-orange)

## 30-second offline quick start

```sh
git clone https://github.com/gbesse/jev-tar.git && cd jev-tar
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m examples.offline_demo
```

The demo probabilities are synthetic fixtures, not measured Jev output.

## Example: zero sampled misses still has an upper bound

Run `python -m examples.zero_miss_interval` for a synthetic elusion sample with no responsive document found. The point estimate is zero, but the Wilson upper interval still leaves possible missed documents. The example makes no legal conclusion; use matter-specific sampling and attorney review for any real workflow.

## Call real Jev

Set `TYPESAFE_API_KEY`, then run `jev-tar classify collection.jsonl --protocol protocol.json --out judgments.jsonl`. Requests are paid and sent to `api.typesafe.ai`. Resume skips ids already present; `audit.jsonl` is appended after every completed document. Run the one-request synthetic smoke test with `python scripts/live_smoke.py`.

## Library and CLI

```python
from jev_tar import classify, family_propagate, FakeJev
judgments = classify(documents, protocol, FakeJev(fixtures))
queue, counts = family_propagate(judgments, .5)
```

Commands include `classify`, `rank`, `plan`, `sample`, `elusion`, `log`, and `export`. CSV and JSONL collections require `id` and `text`; `family_id`, `custodian`, `date`, and `filename` are optional. Concordance `.dat` uses DC4 (`0x14`) fields, thorn qualifiers, and DC3 (`0x13`) record separators.

## How it decides

The protocol supplies exact plain-language noul questions for responsiveness, potential privilege, and each issue. They ride in one request because document state is the costly part. The illustrative review cutoff defaults to 0.5 and must be configured and validated for the matter. Oversized document scores aggregate by maximum probability. Family propagation, random sampling, cutoff split, Wilson intervals, queue order, and exports are code-owned rules; see [the method](docs/method.md).

## Legal boundary

This tool does not practice law, replace attorney review, or claim court acceptance anywhere. Its statistics are only as good as the human coding of the samples. Privilege is a legal determination: the model score is only a triage aid, and every generated privilege-log row is explicitly a draft requiring attorney confirmation.

## Boundaries

Jev can be sensitive to irrelevant state and long documents, so inputs are minimized and chunk aggregation is disclosed. The model version is pinned. No live benchmark, recall guarantee, or legal conclusion is claimed. A random control and holdout must represent the actual collection; synthetic fixtures prove mechanics only.

## Validation

Run `python -m compileall -q src tests`, `python -m unittest discover -s tests`, and `python -m examples.offline_demo`. CI runs those on Python 3.11 and 3.13 after installing `requirements-dev.txt`.

## Related projects

[DecisionPacks](https://github.com/gbesse/decisionpacks), [Question Forge](https://github.com/gbesse/question-forge), and [jev-screen](https://github.com/gbesse/jev-screen) address adjacent policy, question-design, and screening workflows.

Independent project; not affiliated with TypeSafe AI. [API documentation](https://docs.typesafe.ai/api) · [Jev 1.13 model notes](https://docs.typesafe.ai/model-jaggedness/jev-1.13/)
