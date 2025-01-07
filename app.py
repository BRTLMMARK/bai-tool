from fastapi import FastAPI
import requests
import csv
import json
from mangum import Mangum

app = FastAPI()

BAI_URL = "https://docs.google.com/spreadsheets/d/1f7kaFuhCv6S_eX4EuIrlhZFDR7W5MhQpJSXHznlpJEk/export?format=csv"

response_mapping = {
    "Not at all": 0,
    "Several Days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

def get_random_phrase(condition):
    with open("phrases_bai.json", "r") as f:
        phrases = json.load(f)
    return random.choice(phrases[condition])

def get_bai_interpretation(score):
    if score <= 21:
        return "Low Anxiety (0-21)"
    elif score <= 35:
        return "Moderate Anxiety (22-35)"
    else:
        return "Severe Anxiety (36+)"

@app.get("/analyze")
def analyze_bai(client_name: str):
    response = requests.get(BAI_URL)
    response.raise_for_status()
    data = response.text.splitlines()

    reader = csv.reader(data)
    header = next(reader)  # Skip header row

    for row in reader:
        name = row[-1].strip()
        if name.lower() == client_name.lower():
            responses = row[1:-2]
            total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
            interpretation = get_bai_interpretation(total_score)

            primary_impression = (
                "The client may have mild or no anxiety concerns."
                if interpretation == "Low Anxiety (0-21)"
                else "The client might be experiencing anxiety or related concerns."
            )

            additional_impressions = []
            suggested_tools = []

            if interpretation != "Low Anxiety (0-21)":
                additional_impressions = [
                    get_random_phrase("Anxiety"),
                    get_random_phrase("Trauma & PTSD"),
                    get_random_phrase("Youth Mental Health Test"),
                ]
                suggested_tools = [
                    "Tools for Anxiety",
                    "Tools for Trauma & PTSD",
                    "Tools for Youth Mental Health Test",
                ]

            return {
                "client_name": client_name,
                "total_score": total_score,
                "interpretation": interpretation,
                "primary_impression": primary_impression,
                "additional_impressions": additional_impressions,
                "suggested_tools": suggested_tools,
            }

    return {"error": f"Client '{client_name}' not found."}

handler = Mangum(app)
