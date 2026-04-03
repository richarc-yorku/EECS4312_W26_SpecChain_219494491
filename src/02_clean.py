import json
import re
import os
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from num2words import num2words
import string

# Ensure NLTK resources are downloaded
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

INPUT_FILE = "data/reviews_raw.jsonl"
OUTPUT_FILE = "data/reviews_clean.jsonl"

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def clean_text(text: str) -> str:
    if not text:
        return ""

    # Convert numbers to words
    text = re.sub(r'\d+', lambda x: num2words(int(x.group())), text)

    # Lowercase
    text = text.lower()

    # Remove special characters (keep letters and spaces)
    text = re.sub(r"[^a-z\s]", " ", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Tokenize, remove stopwords, lemmatize
    tokens = [lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words]

    # Join back into string
    return " ".join(tokens)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    cleaned_reviews = []
    seen_texts = set()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            review = json.loads(line)
            text = review.get("content", "")
            score = review.get("score", None)
            thumbs_up = review.get("thumbsUpCount", None)

            # Skip empty or extremely short reviews
            if not text or len(text.split()) < 3:
                continue

            cleaned = clean_text(text)

            # Skip reviews that become empty after cleaning
            if not cleaned:
                continue

            # Remove duplicates
            if cleaned in seen_texts:
                continue
            seen_texts.add(cleaned)

            # Save cleaned review
            cleaned_reviews.append({
                "cleaned_content": cleaned,
                "score": score,
                "thumbsUpCount": thumbs_up
            })

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Save to JSONL
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for review in cleaned_reviews:
            f.write(json.dumps(review, ensure_ascii=False) + "\n")

    print(f"Cleaned dataset saved: {OUTPUT_FILE}")
    print(f"Total cleaned reviews: {len(cleaned_reviews)}")

if __name__ == "__main__":
    main()