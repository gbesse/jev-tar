# Purpose: Review pipeline, family rules, statistical validation and production exports.
from __future__ import annotations
import csv, hashlib, json, math, random
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def load_collection(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    else:
        with path.open(newline="") as handle: rows = list(csv.DictReader(handle))
    for row in rows:
        if not row.get("id") or not isinstance(row.get("text"), str): raise ValueError("Each document needs id and text")
    return rows

def _questions(protocol: dict) -> dict:
    values = {"responsive": protocol["responsive"], "privilege": protocol["privilege"]}
    values.update(protocol.get("issues", {}))
    return {key: {"type": "noul", "instructions": value["statement"] if isinstance(value, dict) else value} for key, value in values.items()}

def _chunks(text: str, chars: int) -> list[str]:
    return [text[i:i+chars] for i in range(0, len(text), chars)] or [""]

def classify(rows: list[dict], protocol: dict, provider, *, audit_path: str | Path | None = None,
             existing: list[dict] | None = None, chunk_chars: int = 72_000) -> list[dict]:
    """Classify once per document (or chunk); max probability aggregation avoids hiding a hot passage."""
    done = {row["id"]: row for row in (existing or [])}
    questions, fingerprint = _questions(protocol), hashlib.sha256(canonical(protocol).encode()).hexdigest()
    output = list(existing or [])
    audit = Path(audit_path) if audit_path else None
    for row in rows:
        if row["id"] in done: continue
        answers = [provider.judge({"id": row["id"], "text": chunk}, questions)["answers"] for chunk in _chunks(row["text"], chunk_chars)]
        probabilities = {key: max(float(answer[key].get("noul", answer[key]["probabilities"]["true"])) for answer in answers) for key in questions}
        judged = {**row, "probabilities": probabilities, "responsive_score": probabilities["responsive"],
                  "privilege_score": probabilities["privilege"], "chunk_count": len(answers), "model": "jev-1.13.0"}
        output.append(judged)
        if audit:
            audit.parent.mkdir(parents=True, exist_ok=True)
            with audit.open("a") as handle:
                handle.write(canonical({"document_id": row["id"], "model": "jev-1.13.0", "protocol_fingerprint": fingerprint,
                                        "probabilities": probabilities, "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n")
    return output

def family_propagate(rows: list[dict], cutoff: float) -> tuple[list[dict], dict]:
    hot = {row.get("family_id") for row in rows if row.get("family_id") and row["responsive_score"] >= cutoff}
    direct = propagated = 0; result = []
    for row in rows:
        own = row["responsive_score"] >= cutoff
        pulled = not own and row.get("family_id") in hot
        direct += own; propagated += pulled
        result.append({**row, "in_review": own or pulled, "family_propagated": pulled})
    return result, {"direct": direct, "family_propagated": propagated, "total_review": direct + propagated}

def rank_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (r.get("privilege_score", 0) >= .5, r.get("responsive_score", 0)), reverse=True)

def plan_sample(population: int, margin: float, confidence: float, proportion: float = .5) -> dict:
    z = NormalDist().inv_cdf((1 + confidence) / 2); n0 = z*z*proportion*(1-proportion)/(margin*margin)
    n = math.ceil(n0 / (1 + (n0 - 1) / population)) if population else math.ceil(n0)
    return {"sample_size": n, "infinite_population": math.ceil(n0), "formula": "n0=z²p(1-p)/e²; n=n0/(1+(n0-1)/N)"}

def wilson_interval(successes: int, total: int, confidence: float = .95) -> tuple[float, float]:
    if total <= 0: raise ValueError("total must be positive")
    z = NormalDist().inv_cdf((1+confidence)/2); p = successes/total; d = 1+z*z/total
    center=(p+z*z/(2*total))/d; half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return max(0, center-half), min(1, center+half)

def sample_elusion(rows: list[dict], cutoff: float, n: int, seed: int) -> list[dict]:
    candidates = [row for row in rows if row["responsive_score"] < cutoff]
    picked = random.Random(seed).sample(candidates, min(n, len(candidates)))
    return [{**row, "human_responsive": ""} for row in picked]

def elusion_estimate(sample: list[dict], population_below: int, reviewed_found: int = 0) -> dict:
    labels = [str(row["human_responsive"]).lower() in {"1", "true", "yes"} for row in sample if str(row.get("human_responsive", "")).strip()]
    if not labels: raise ValueError("Sample has no human labels")
    misses=sum(labels); low, high=wilson_interval(misses,len(labels)); estimated=misses/len(labels)*population_below
    recall = reviewed_found/(reviewed_found+estimated) if reviewed_found+estimated else None
    return {"sample": len(labels), "misses": misses, "elusion_rate": misses/len(labels), "rate_interval": [low,high],
            "estimated_missed": estimated, "missed_interval": [low*population_below, high*population_below], "estimated_recall": recall}

def select_cutoff(judgments: list[dict], control: list[dict], target_recall: float, seed: int = 7, holdout_fraction: float = .3) -> dict:
    """Tune and validate on disjoint random ids; return ids so the separation is auditable."""
    shuffled=list(control); random.Random(seed).shuffle(shuffled); split=max(1, int(len(shuffled)*(1-holdout_fraction)))
    tune, holdout=shuffled[:split], shuffled[split:]
    scores={str(row["id"]): float(row["responsive_score"]) for row in judgments}
    positives=[scores[str(r["id"])] for r in tune if str(r["human_responsive"]).lower() in {"1","true","yes"}]
    if not positives: raise ValueError("Tuning split has no responsive rows")
    candidates=sorted(set(scores.values()), reverse=True); cutoff=min(candidates)
    for value in candidates:
        if sum(score >= value for score in positives)/len(positives) >= target_recall: cutoff=value; break
    hp=[r for r in holdout if str(r["human_responsive"]).lower() in {"1","true","yes"}]
    found=sum(scores[str(r["id"])] >= cutoff for r in hp); interval=wilson_interval(found,len(hp)) if hp else (0,1)
    return {"cutoff": cutoff, "tune_ids": [r["id"] for r in tune], "holdout_ids": [r["id"] for r in holdout],
            "holdout_recall": found/len(hp) if hp else None, "holdout_interval": interval}

def privilege_log(rows: list[dict], cutoff: float=.5) -> list[dict]:
    return [{"document_id": r["id"], "date": r.get("date", ""), "custodian": r.get("custodian", ""),
             "description": r.get("filename", "Document"), "status": "DRAFT — attorney confirmation required"}
            for r in rows if r.get("privilege_score",0)>=cutoff]

def export_production(rows: list[dict], directory: str | Path) -> dict:
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True); fields=["id","filename","responsive_score","privilege_score"]
    with (directory/"production.csv").open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k,"") for k in fields} for r in rows)
    # Concordance uses DC4 as field separator, quote as text qualifier and DC3 as newline.
    sep, newline="\x14", "\x13\n"
    data=sep.join(fields)+newline+"".join(sep.join(f'þ{r.get(k, "")}þ' for k in fields)+newline for r in rows)
    (directory/"production.dat").write_text(data)
    manifest={"documents":len(rows),"responsive":sum(r.get("responsive_score",0)>=.5 for r in rows),"privileged":sum(r.get("privilege_score",0)>=.5 for r in rows)}
    (directory/"manifest.json").write_text(json.dumps(manifest,indent=2)); return manifest
