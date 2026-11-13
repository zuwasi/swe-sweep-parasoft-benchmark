#!/usr/bin/env python3
"""Merge pass-1 and pass-2 blind labels into final per-bug classification.

Rules:
- Agreement between passes: keep the class, confidence high.
- Disagreement: reported for adjudication in classification/adjudication.csv;
  adjudicated overrides live in classification/labels_final_overrides.jsonl.
- Snippet-empty bugs (no lines in snippets_v2) are UNKNOWN.
"""
import csv
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLS = os.path.join(ROOT, "classification")

SA_CLASSES = {"MEMORY", "RESOURCE", "ERROR"}
SA_RANK = {"MEMORY": 0, "RESOURCE": 1, "ERROR": 2}
NONSA_RANK = {"LOGIC": 0, "OTHER": 1}


def load_labels(dirname):
    out = {}
    for path in glob.glob(os.path.join(CLS, dirname, "*.jsonl")):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            out[d["bug_id"]] = d
    return out


def load_empty_ids():
    ids = set()
    for path in glob.glob(os.path.join(CLS, "snippets_v2", "*.jsonl")):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if not d.get("lines"):
                ids.add(d["bug_id"])
    return ids


def main():
    p1 = load_labels("labels_pass1")
    p2 = load_labels("labels_v2")
    empty = load_empty_ids()
    overrides = {}
    ovr_path = os.path.join(CLS, "labels_final_overrides.jsonl")
    if os.path.exists(ovr_path):
        for line in open(ovr_path, encoding="utf-8"):
            line = line.strip()
            if line:
                d = json.loads(line)
                overrides[d["bug_id"]] = d

    agree = disagree = missing = 0
    adjudication_rows = []
    final = {}
    all_ids = sorted(set(p1) | set(p2))
    for bug_id in all_ids:
        if bug_id in overrides:
            d = overrides[bug_id]
            d["pass1"] = p1.get(bug_id, {}).get("sa_class", "")
            d["pass2"] = p2.get(bug_id, {}).get("sa_class", "")
            final[bug_id] = d
            continue
        if bug_id in empty:
            final[bug_id] = {
                "bug_id": bug_id, "sa_class": "UNKNOWN",
                "confidence": "low", "reason": "no snippet extractable",
                "pass1": p1.get(bug_id, {}).get("sa_class", ""),
                "pass2": p2.get(bug_id, {}).get("sa_class", ""),
            }
            continue
        a, b = p1.get(bug_id), p2.get(bug_id)
        if a is None or b is None:
            missing += 1
            adjudication_rows.append((bug_id, "", "", "MISSING_LABEL"))
            continue
        if a["sa_class"] == b["sa_class"]:
            agree += 1
            conf = a["confidence"] if a["confidence"] == b["confidence"] else "low"
            final[bug_id] = {
                "bug_id": bug_id, "sa_class": a["sa_class"], "confidence": conf,
                "reason": a.get("reason", ""), "pass1": a["sa_class"],
                "pass2": b["sa_class"],
            }
        elif (a["sa_class"] in SA_CLASSES) == (b["sa_class"] in SA_CLASSES):
            # Same side of the SA boundary: automatic resolution.
            conf_a = a.get("confidence", "low")
            conf_b = b.get("confidence", "low")
            if conf_a != conf_b:
                pick = a if conf_a == "high" else b
            else:
                rank = SA_RANK if a["sa_class"] in SA_CLASSES else NONSA_RANK
                pick = a if rank[a["sa_class"]] <= rank[b["sa_class"]] else b
            disagree += 1
            adjudication_rows.append((bug_id, a["sa_class"], b["sa_class"],
                                      f"AUTO_{pick['sa_class']}"))
            final[bug_id] = {
                "bug_id": bug_id, "sa_class": pick["sa_class"],
                "confidence": "low",
                "reason": f"same-side tie-break ({pick['sa_class']})",
                "pass1": a["sa_class"], "pass2": b["sa_class"],
            }
        else:
            disagree += 1
            adjudication_rows.append((bug_id, a["sa_class"], b["sa_class"], ""))

    out_dir = os.path.join(CLS, "final")
    os.makedirs(out_dir, exist_ok=True)
    by_repo = {}
    for path in glob.glob(os.path.join(CLS, "snippets_v2", "*.jsonl")):
        repo = os.path.basename(path)[:-6]
        by_repo[repo] = []
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            bug_id = json.loads(line)["bug_id"]
            by_repo[repo].append(final.get(bug_id))
    for repo, rows in by_repo.items():
        with open(os.path.join(out_dir, f"{repo}.jsonl"), "w", encoding="utf-8") as fh:
            for d in rows:
                if d is None:
                    fh.write(json.dumps({"bug_id": "MISSING", "sa_class": "UNKNOWN",
                                         "confidence": "low", "reason": "unlabeled"}) + "\n")
                else:
                    fh.write(json.dumps(d) + "\n")
    with open(os.path.join(out_dir, "all.jsonl"), "w", encoding="utf-8") as fh:
        for repo in sorted(by_repo):
            for d in by_repo[repo]:
                if d is not None:
                    fh.write(json.dumps(d) + "\n")
    with open(os.path.join(CLS, "adjudication.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["bug_id", "pass1", "pass2", "note"])
        w.writerows(adjudication_rows)

    print(f"agree={agree} disagree={disagree} missing={missing} total={len(all_ids)}")


if __name__ == "__main__":
    main()
