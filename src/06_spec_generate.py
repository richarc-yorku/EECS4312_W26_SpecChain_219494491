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

# Extract markdown
def extract_text_block(text):
    # Try to find first requirement ID marker
    match = re.search(r"# Requirement ID: AFR\d+", text)
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
- Requirement ID must be FR plus number (FR1, FR2, ...)
- Include: Description, Source Persona, Traceability, Acceptance Criteria
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
    
    print(f"Specifications saved to {SPEC_OUTPUT}")

if __name__ == "__main__":
    main()