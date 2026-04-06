import os
import sys
import subprocess

# List of scripts in execution order
SCRIPTS = [
    "00_validate_repo.py",          # validate repository structure
    "01_collect_or_import.py",      # collect/import raw dataset    - creates reviews_raw.jsonl
    "02_clean.py",                  # clean dataset                 - creates reviews_clean.jsonl
    # "03_manual_coding_template.py", # manual coding template
    # "04_personas_manual.py",        # generate manual personas
    "05_personas_auto.py",          # generate automated personas   - creates personas_auto.json
    "06_spec_generate.py",          # generate specifications       - creates spec_auto.md
    "07_tests_generate.py",         # generate tests                - creates tests_auto.json
    "08_metrics.py"                 # compute metrics               - creates metrics_auto/hyrbid/manual/summary
]

def run_script(script_name):
    script_path = os.path.join("src", script_name)
    print(f"\nRunning {script_name}...")
    try:
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {script_name} failed with return code {result.returncode}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"ERROR: Failed to run {script_name}: {e}")
        return False

def main():
    # 1. Check for GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable not set. Exiting.")
        sys.exit(1)
    else:
        print("GROQ_API_KEY found.")

    # 2. Run repository validation first
    if not run_script("00_validate_repo.py"):
        print("Repository validation failed. Exiting.")
        sys.exit(1)

    # 3. Run remaining workflow scripts in order
    for script in SCRIPTS[1:]:
        if not run_script(script):
            print(f"Workflow stopped due to failure in {script}. Exiting.")
            sys.exit(1)

    print("\nAll steps executed successfully!")

if __name__ == "__main__":
    main()