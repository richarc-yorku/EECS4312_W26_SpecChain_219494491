import json
import re
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SPEC_INPUT = "spec/spec_auto.md"
TEST_OUTPUT = "tests/tests_auto.json"
SYSTEM_PROMPT = "You are a test automation analyst. Generate clear validation scenarios for each system requirement."

PROMPT_FILE = "prompts/prompt_auto.json"


# Utility: Parse requirements from markdown
def parse_requirements(markdown_text):
    # Split by requirement headers
    req_blocks = re.split(r'# Requirement ID: (FR\d+)', markdown_text)
    
    requirements = []
    # After split, req_blocks[0] is everything before first FR, then we have pairs of [id, content]
    for i in range(1, len(req_blocks), 2):
        req_id = req_blocks[i].strip()
        content = req_blocks[i+1].strip()

        # Extract each field
        description_match = re.search(r'\* Description:\s*(.*?)\n(?=\*|$)', content, re.DOTALL)
        source_match = re.search(r'\* Source Persona:\s*(.*?)\n(?=\*|$)', content, re.DOTALL)
        trace_match = re.search(r'\* Traceability:\s*(.*?)\n(?=\*|$)', content, re.DOTALL)
        acceptance_match = re.search(r'\* Acceptance Criteria:\s*(.*?)\n(?=\*|$)', content, re.DOTALL)

        requirements.append({
            "requirement_id": req_id,
            "description": description_match.group(1).strip() if description_match else "",
            "source_persona": source_match.group(1).strip() if source_match else "",
            "traceability": trace_match.group(1).strip() if trace_match else "",
            "acceptance_criteria": acceptance_match.group(1).strip() if acceptance_match else ""
        })

    return requirements


# Step 4.4: Build validation test generation prompt
def build_test_prompt(requirements):
    req_texts = []
    for r in requirements:
        req_texts.append(json.dumps(r, indent=2))

    return f"""
You are a JSON generator.

IMPORTANT:
- Output ONLY valid JSON
- Generate at least two validation test scenario per requirement
- Each test scenario must include:
  - test_id: unique identifier (T1, T2, ...)
  - requirement_id: the requirement it validates
  - scenario_description: brief description of the validation scenario
  - steps: list of steps describing how to perform the test
  - expected_outcome: the expected result that satisfies the requirement

- tests must be actionable and specific, use professional language
- steps and expected outcomes must be qualitative

Requirements:
{chr(10).join(req_texts)}

Return strictly in this format:

{{
  "tests": [
    {{
      "test_id": "T1",
      "requirement_id": "FR1",
      "scenario_description": "...",
      "steps": ["step 1", "step 2"],
      "expected_outcome": "..."
    }}
  ]
}}
"""


# Generate test scenarios via Groq API
def generate_tests(requirements):
    prompt = build_test_prompt(requirements)

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    raw_output = response.choices[0].message.content

    # Attempt to extract valid JSON
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        # Fallback: extract content inside outermost braces
        start = raw_output.find("{")
        end = raw_output.rfind("}") + 1
        json_str = raw_output[start:end].replace('\n', ' ').replace('\t', ' ')
        data = json.loads(json_str)

    # Ensure unique test IDs
    for i, test in enumerate(data.get("tests", []), start=1):
        test["test_id"] = f"T{i}"

    return data


# MAIN PIPELINE
def main():
    # Load specification markdown
    with open(SPEC_INPUT, "r", encoding="utf-8") as f:
        spec_md = f.read()

    # Parse requirements
    requirements = parse_requirements(spec_md)

    # Generate test scenarios
    tests = generate_tests(requirements)

    # Save to JSON file
    os.makedirs(os.path.dirname(TEST_OUTPUT), exist_ok=True)
    with open(TEST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(tests, f, indent=2)

    update_prompts(build_test_prompt(requirements))
    print(f"Validation tests saved to {TEST_OUTPUT}")

def update_prompts(test_user_prompt):
    # Load existing prompts if the file exists
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r") as f:
            prompts_data = json.load(f)
    else:
        prompts_data = {}

    # Ensure the structure exists
    prompts_data.setdefault("model", "meta-llama/llama-4-scout-17b-16e-instruct")
    prompts_data.setdefault("group_Generation", {"system_prompt": "", "user_prompt": ""})
    prompts_data.setdefault("persona_generation", {"system_prompt": "", "user_prompt": ""})
    prompts_data.setdefault("spec_generation", {"system_prompt": "", "user_prompt": ""})
    prompts_data.setdefault("test_generation", {"system_prompt": "", "user_prompt": ""})

    # Update only the user prompts
    prompts_data["test_generation"]["system_prompt"] = SYSTEM_PROMPT
    prompts_data["test_generation"]["user_prompt"] = test_user_prompt

    # Write back
    os.makedirs(os.path.dirname(PROMPT_FILE), exist_ok=True)
    with open(PROMPT_FILE, "w") as f:
        json.dump(prompts_data, f, indent=2)
    print(f"Prompts updated in {PROMPT_FILE}")

if __name__ == "__main__":
    main()