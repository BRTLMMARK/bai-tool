from fastapi import FastAPI, HTTPException
import requests
import csv
import json
import random
from mangum import Mangum

app = FastAPI()

BAI_URL = "https://docs.google.com/spreadsheets/d/1f7kaFuhCv6S_eX4EuIrlhZFDR7W5MhQpJSXHznlpJEk/export?format=csv"

response_mapping = {
    "Not at all": 0,
    "Mildly, but it didn't bother me much": 1,
    "Moderately - it wasn't pleasant at times": 2,
    "Severely - it bothered me a lot": 3
}

# Load phrases for BAI
with open("phrases_bai.json", "r") as f:
    phrases = json.load(f)

def get_random_phrase(condition, used_phrases):
    available_phrases = [p for p in phrases[condition] if p not in used_phrases]
    if available_phrases:
        phrase = random.choice(available_phrases)
        used_phrases.add(phrase)
        return phrase
    else:
        return "No more unique phrases available."

def get_bai_interpretation(score):
    if score <= 21:
        return "Low Anxiety (0-21)"
    elif score <= 35:
        return "Moderate Anxiety (22-35)"
    else:
        return "Severe Anxiety (36+)"

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "PHQ-9 Tool API is running and accessible."}

@app.get("/analyze")
def analyze_bai(client_name: str):
    response = requests.get(BAI_URL)
    response.raise_for_status()
    data = response.text.splitlines()

    reader = csv.reader(data)
    header = next(reader)

    used_phrases = set()

    for row in reader:
        name = row[-1].strip()
        if name.lower() == client_name.lower():
            responses = row[1:-2]
            total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
            interpretation = get_bai_interpretation(total_score)

            if interpretation == "Low Anxiety (0-21)":
                return {
                    "client_name": client_name,
                    "total_score": total_score,
                    "interpretation": interpretation,
                    "message": f"The results indicate {client_name} has low anxiety levels, with no further concerns."
                }

            primary_impression = f"The analysis suggests {client_name} may be experiencing {interpretation.lower()}."
            additional_impressions = [
                get_random_phrase("Anxiety", used_phrases),
                get_random_phrase("Trauma & PTSD", used_phrases),
                get_random_phrase("Youth Mental Health Test", used_phrases)
            ]

            return {
                "client_name": client_name,
                "total_score": total_score,
                "interpretation": interpretation,
                "primary_impression": primary_impression,
                "additional_impressions": additional_impressions
            }

    raise HTTPException(status_code=404, detail=f"Client '{client_name}' not found.")

handler = Mangum(app)
