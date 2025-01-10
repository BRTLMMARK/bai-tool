from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import csv
import json
import random
from mangum import Mangum

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (use specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

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

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "message": "BAI Tool API is running and accessible."}

@app.get("/analyze")
def analyze_bai(first_name: str, last_name: str, middle_name: str = "", suffix: str = ""):
    try:
        response = requests.get(BAI_URL)
        response.raise_for_status()
        data = response.text.splitlines()

        reader = csv.reader(data)
        header = next(reader)

        used_phrases = set()

        # Normalize input for comparison
        input_name = f"{first_name} {middle_name} {last_name} {suffix}".strip().lower()

        for row in reader:
            # Extract and normalize name from the CSV
            row_name = f"{row[-4]} {row[-3]} {row[-2]} {row[-1]}".strip().lower()

            if row_name == input_name:
                responses = row[1:-4]  # Exclude timestamp and name fields
                total_score = sum(response_mapping.get(r.strip(), 0) for r in responses)
                interpretation = get_bai_interpretation(total_score)

                if interpretation == "Low Anxiety (0-21)":
                    return {
                        "client_name": input_name.title(),
                        "total_score": total_score,
                        "interpretation": interpretation,
                        "message": f"The results indicate {input_name.title()} has low anxiety levels, with no further concerns."
                    }

                primary_impression = f"The analysis suggests {input_name.title()} may be experiencing {interpretation.lower()}."
                additional_impressions = [
                    get_random_phrase("Anxiety", used_phrases),
                    get_random_phrase("Trauma & PTSD", used_phrases),
                    get_random_phrase("Youth Mental Health Test", used_phrases)
                ]

                return {
                    "client_name": input_name.title(),
                    "total_score": total_score,
                    "interpretation": interpretation,
                    "primary_impression": primary_impression,
                    "additional_impressions": additional_impressions
                }

        raise HTTPException(status_code=404, detail=f"Client '{input_name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing BAI data: {e}")

handler = Mangum(app)
