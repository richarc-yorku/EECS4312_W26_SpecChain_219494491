import json
import re

# Define all pipelines and their file paths
PIPELINES = {
    "manual": {
        "reviews": "data/reviews_clean.jsonl",
        "groups": "data/review_groups_manual.json",
        "personas": "personas/personas_manual.json",
        "spec": "spec/spec_manual.md",
        "tests": "tests/tests_manual.json",
        "metrics": "metrics/metrics_manual.json"
    },
    "auto": {
        "reviews": "data/reviews_clean.jsonl",
        "groups": "data/review_groups_auto.json",
        "personas": "personas/personas_auto.json",
        "spec": "spec/spec_auto.md",
        "tests": "tests/tests_auto.json",
        "metrics": "metrics/metrics_auto.json"
    },
    "hybrid": {
        "reviews": "data/reviews_clean.jsonl",
        "groups": "data/review_groups_hybrid.json",
        "personas": "personas/personas_hybrid.json",
        "spec": "spec/spec_hybrid.md",
        "tests": "tests/tests_hybrid.json",
        "metrics": "metrics/metrics_hybrid.json"
    }
}

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_metrics_for_pipeline(pipeline_name, files):
    # Load reviews
    with open(files["reviews"], "r", encoding="utf-8") as f:
        reviews = [json.loads(line) for line in f]
    dataset_size = len(reviews)

    # Load artifacts
    groups_data = load_json(files["groups"]).get("groups", [])
    personas = load_json(files["personas"]).get("personas", [])
    tests = load_json(files["tests"]).get("tests", [])

    with open(files["spec"], "r", encoding="utf-8", errors="replace") as f:
        spec_text = f.read()

    # Counts
    persona_count = len(personas)
    requirements = re.findall(r"# Requirement ID: (FR\d+)", spec_text)
    requirements_count = len(requirements)
    tests_count = len(tests)

    # group → persona links
    group_ids_set = {g["group_id"] for g in groups_data}
    group_to_persona = sum(1 for p in personas if p.get("derived_from_group") in group_ids_set)

    # persona → requirement links (from spec)
    persona_to_req = 0
    for p in personas:
        pattern = re.compile(rf"Source Persona: {re.escape(p.get('name',''))}")
        persona_to_req += len(pattern.findall(spec_text))

    # requirement → test links
    req_ids_set = set(requirements)
    req_to_test = sum(1 for t in tests if t.get("requirement_id") in req_ids_set)

    traceability_links = group_to_persona + persona_to_req + req_to_test

    # Review coverage
    persona_review_ids = set()
    for p in personas:
        for revs in p.get("evidence_reviews", []):
            ids = re.findall(r'\d+', str(revs))
            persona_review_ids.update(ids)
    review_coverage = len(persona_review_ids) / max(dataset_size, 1)

    # Traceability ratio
    traceability_ratio = persona_to_req / max(requirements_count, 1)

    # Testability rate
    tested_requirements = {t.get("requirement_id") for t in tests}
    testability_rate = len(set(requirements) & tested_requirements) / max(requirements_count, 1)

    # Ambiguity ratio
    ambiguous_terms = ["fast", "easy", "better", "user-friendly", "intuitive", "simple", "seamless"]
    ambiguous_count = sum(1 for line in spec_text.splitlines() if any(term in line.lower() for term in ambiguous_terms))
    ambiguity_ratio = ambiguous_count / max(requirements_count, 1)

    metrics = {
        "pipeline": pipeline_name,
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": traceability_links,
        "review_coverage": round(review_coverage, 4),
        "traceability_ratio": round(traceability_ratio, 2),
        "testability_rate": round(testability_rate, 2),
        "ambiguity_ratio": round(ambiguity_ratio, 2)
    }

    # Save metrics
    with open(files["metrics"], "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics for '{pipeline_name}' saved to {files['metrics']}")
    return metrics

if __name__ == "__main__":
    all_metrics = {}
    for name, files in PIPELINES.items():
        all_metrics[name] = compute_metrics_for_pipeline(name, files)