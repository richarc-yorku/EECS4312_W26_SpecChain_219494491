import json
import re

# Paths to artifacts
REVIEWS_FILE = "data/reviews_clean.jsonl"
GROUPS_FILE = "data/review_groups_hybrid.json"
PERSONAS_FILE = "personas/personas_hybrid.json"
SPEC_FILE = "spec/spec_hybrid.md"
TESTS_FILE = "tests/tests_hybrid.json"

METRICS_FILE = "metrics/metrics_hybrid.json"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def compute_metrics():
    # Load reviews
    with open(REVIEWS_FILE, "r") as f:
        reviews = [json.loads(line) for line in f]
    dataset_size = len(reviews)

    # Load artifacts
    groups_data = load_json(GROUPS_FILE)["groups"]
    personas = load_json(PERSONAS_FILE)["personas"]
    tests = load_json(TESTS_FILE)["tests"]
    
    with open(SPEC_FILE, "r", encoding="utf-8") as f:
        spec_text = f.read()
    
    # Basic counts
    persona_count = len(personas)
    requirements = re.findall(r"# Requirement ID: (FR\d+)", spec_text)
    requirements_count = len(requirements)
    tests_count = len(tests)

    # group → persona links
    group_ids_set = {g["group_id"] for g in groups_data}
    group_to_persona = sum(1 for p in personas if p["derived_from_group"] in group_ids_set)

    # persona → requirement links (from spec)
    persona_to_req = 0
    for p in personas:
        pattern = re.compile(rf"Source Persona: {re.escape(p['name'])}")
        persona_to_req += len(pattern.findall(spec_text))

    # requirement → test links
    req_ids_set = set(requirements)
    req_to_test = sum(1 for t in tests if t["requirement_id"] in req_ids_set)

    # Total traceability links
    traceability_links = group_to_persona + persona_to_req + req_to_test

    # Review coverage: ratio of reviews referenced in personas
    persona_review_ids = set()
    for p in personas:
        for revs in p.get("evidence_reviews", []):
            ids = re.findall(r'\d+', revs)
            persona_review_ids.update(ids)
    review_coverage = len(persona_review_ids) / max(dataset_size, 1)

    # Traceability ratio: proportion of requirements linked to a persona
    traceability_ratio = persona_to_req / max(requirements_count, 1)

    # Testability rate: proportion of requirements with at least one test
    tested_requirements = {t["requirement_id"] for t in tests}
    testability_rate = len(set(requirements) & tested_requirements) / max(requirements_count, 1)

    # Ambiguity ratio: check for vague terms in requirement text
    ambiguous_terms = ["fast", "easy", "better", "user-friendly", "intuitive", "simple", "seamless"]
    ambiguous_count = sum(1 for line in spec_text.splitlines() if any(term in line.lower() for term in ambiguous_terms))
    ambiguity_ratio = ambiguous_count / max(requirements_count, 1)

    metrics = {
        "pipeline": "hybrid",
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

    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    print("Automated pipeline metrics saved to", METRICS_FILE)
    return metrics

if __name__ == "__main__":
    compute_metrics()