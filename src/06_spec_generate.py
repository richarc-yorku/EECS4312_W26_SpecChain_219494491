import json
import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PERSONA_INPUT = "personas/personas_auto.json"
SPEC_OUTPUT = "spec/spec_auto.md"
SYSTEM_PROMPT = "You are a requirements engineering analyst."

PROMPT_FILE = "prompts/prompt_auto.json"

# Extract markdown
def extract_text_block(text):
    # Try to find first requirement ID marker
    match = re.search(r"# Requirement ID: FR\d+", text)
    if match:
        return text[match.start():].strip()
    return text.strip()


# Step 4.3: Build specification prompt
def build_spec_prompt(personas):
    persona_texts = []
    for p in personas["personas"]:
        persona_texts.append(json.dumps(p, indent=2))

    return f"""
IMPORTANT:
- Output ONLY valid Markdown following this template
- Do NOT include any explanation, preamble, or code blocks
- Generate 2-3 system requirements per persona
- Generate at least 10 requirements
- Requirement ID must be FR plus number (FR1, FR2, ...)
- Include the following fields for each requirement:

# Requirement ID: <FR#>

* Description: <Describe the functionality the system must provide>
* Source Persona: <Persona name used to generate this requirement>
* Traceability: Derived from review group: <G1, G2, ...>
* Acceptance Criteria: <Qualitative criteria in "Given/When/Then" format>

- Traceability must reference the review group used to generate the persona in the form "Derived from review group: G1, G2, ..."
- Acceptance Criteria must include qualitative criteria

Persona Data:
{chr(10).join(persona_texts)}

Output requirements for all personas in a single Markdown response.
"""


# Step 4.3: Generate specifications
def generate_specifications(personas):
    prompt = build_spec_prompt(personas)

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    raw_output = response.choices[0].message.content
    markdown = extract_text_block(raw_output)

    return markdown


# MAIN PIPELINE
def main():
    # Load automated personas
    with open(PERSONA_INPUT, "r", encoding="utf-8") as f:
        personas = json.load(f)

    # Generate specifications
    specifications = generate_specifications(personas)
    with open(SPEC_OUTPUT, "w", encoding="utf-8") as f:
        f.write(specifications)

    update_prompts(build_spec_prompt(personas))
    
    print(f"Specifications saved to {SPEC_OUTPUT}")

def update_prompts(spec_user_prompt):
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
    prompts_data["spec_generation"]["system_prompt"] = SYSTEM_PROMPT
    prompts_data["spec_generation"]["user_prompt"] = spec_user_prompt

    # Write back
    os.makedirs(os.path.dirname(PROMPT_FILE), exist_ok=True)
    with open(PROMPT_FILE, "w") as f:
        json.dump(prompts_data, f, indent=2)
    print(f"Prompts updated in {PROMPT_FILE}")

if __name__ == "__main__":
    main()