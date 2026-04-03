from google_play_scraper import reviews, Sort
import json

APP_ID = "com.getsomeheadspace.android"
TARGET_COUNT = 1000

all_reviews = []
continuation_token = None

while len(all_reviews) < TARGET_COUNT:
    batch, continuation_token = reviews(
        APP_ID,
        lang="en",
        country="ca",
        sort=Sort.NEWEST,
        count=200,
        continuation_token=continuation_token
    )

    if not batch:
        break

    all_reviews.extend(batch)

all_reviews = all_reviews[:TARGET_COUNT]

if len(all_reviews) < TARGET_COUNT:
    print(f"Warning: Only collected {len(all_reviews)} reviews."
          f"Target was {TARGET_COUNT}.")
else:
    print(f"Successfully collected {len(all_reviews)} reviews.")

with open("data/reviews_raw.jsonl", "w", encoding="utf-8") as f:
    for idx, review in enumerate(all_reviews):
        review["review_id"] = idx + 1
        f.write(json.dumps(review, ensure_ascii=False, default=str) + "\n")

print(f"Saved {len(all_reviews)} reviews.")