import json
import os
import random
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

REVIEW_INPUT = "data/reviews_clean.jsonl"
GROUP_OUTPUT = "data/review_groups_auto.json"
PERSONA_OUTPUT = "personas/personas_auto.json"
SYSTEM_PROMPT = "You are a requirements engineering analyst."

# Utility: Extract JSON
def extract_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Keep only content inside outermost braces
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in response")
        json_str = text[start:end]

        # Remove stray newlines/tabs
        json_str = json_str.replace('\n', ' ').replace('\t', ' ')
        return json.loads(json_str)


# Step 4.1: Build grouping prompt
def build_grouping_prompt(reviews, sample_size=100):
    if len(reviews) > sample_size:
        reviews = random.sample(reviews, sample_size)

    review_text = [
        f'{r["id"]}: {r["cleaned_content"]}'
        for r in reviews
    ]

    return f"""
You are a JSON generator.

IMPORTANT:
- Output ONLY valid JSON
- Do NOT include any explanation, text, or preamble
- Do NOT use markdown (no ``` blocks)
- Do NOT include comments
- The response must start with '{{' and end with '}}'

- return 5 groups
- include 10-15 review ids per group in a single line
- include at least 5 example_reviews per group

Return strictly this format:

{{
  "groups": [
    {{
      "group_id": "G1",
      "theme": "...",
      "review_ids": ["1, 2"],
      "example_reviews": ["...", "..."]
    }}
  ]
}}

Reviews:
{chr(10).join(review_text)}
"""


# Step 4.1: Generate groups
def generate_groups(reviews):
    prompt = build_grouping_prompt(reviews)

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
            ],
        temperature=0.2
    )

    raw_output = response.choices[0].message.content
    data = extract_json(raw_output)

    return data["groups"]


# -------------------------
# Step 4.2: Persona prompt
# -------------------------
def build_personas_prompt(groups):
    group_texts = []
    for group in groups:
        group_texts.append(
            f"""
Group ID: {group['group_id']}
Theme: {group['theme']}
Review IDs: {', '.join(group['review_ids'])}
Example Reviews:
{chr(10).join(group['example_reviews'])}
"""
        )

    return f"""
You are a JSON generator.

IMPORTANT:
- Output ONLY valid JSON
- Do NOT include explanations, preamble, or markdown
- evidence_reviews should contain the numeric IDs of each group's reviews
- Generate ONE persona per group
- Include a name that describes a typical user from each group
- Include all relevant reviews under "evidence_reviews" in a single line

Return strictly this format:

{{
  "personas": [
    {{
      "id": "P1",
      "name": "...",
      "description": "...",
      "derived_from_group": "G1",
      "goals": ["...", "..."],
      "pain_points": ["...", "..."],
      "context": ["...", "..."],
      "constraints": ["...", "..."],
      "evidence_reviews": ["1, 2"]
    }}
  ]
}}

Groups:
{chr(10).join(group_texts)}
"""


# Step 4.2: Generate personas
def generate_personas(groups):
    prompt = build_personas_prompt(groups)

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    raw_output = response.choices[0].message.content
    data = extract_json(raw_output)

    # Assign consistent IDs
    for i, persona in enumerate(data["personas"], start=1):
        persona["id"] = f"P{i}"

    return data


# MAIN PIPELINE
def main():
    # Load cleaned reviews
    with open(REVIEW_INPUT, "r") as f:
        reviews = [json.loads(line) for line in f]

    # Step 4.1
    groups = generate_groups(reviews)
    with open(GROUP_OUTPUT, "w") as f:
        json.dump({"groups": groups}, f, indent=2)

    # Step 4.2
    personas = generate_personas(groups)
    with open(PERSONA_OUTPUT, "w") as f:
        json.dump(personas, f, indent=2)

    print("Auto personas pipeline completed.")


if __name__ == "__main__":
    main()