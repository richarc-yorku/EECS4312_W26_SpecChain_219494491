import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

REQUIRED_FILES = [
    "data/reviews_raw.jsonl",
    "data/reviews_clean.jsonl",
    "data/dataset_metadata.json",
    "data/review_groups_manual.json",
    "data/review_groups_hybrid.json",

    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",

    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",

    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",

    "README.md",

    "reflection/reflection.md",

    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",

    "Src/00_validate_repo.py",
    "Src/01_collect_or_import.py",
    "Src/02_clean.py",
    "Src/03_manual_coding_template.py",
    "Src/04_personas_manual.py",
    "Src/05_personas_auto.py",
    "Src/06_spec_generate.py",
    "Src/07_tests_generate.py",
    "Src/08_metrics.py",
    "Src/run_all.py",
]

def validate_repo(base_path = REPO_ROOT):
    
    missing = []

    for file in REQUIRED_FILES:
        full_path = os.path.join(base_path, file)
        if not os.path.exists(full_path):
            missing.append(file)
    
    if missing:
        print("repository validation failed.")
        print("missing files:")
        for item in missing:
            print(f"- {item}")
        return False
    else:
        print("Repository validation successful.\nAll files are present.")
        return True
    
if __name__ == "__main__":
    validate_repo()