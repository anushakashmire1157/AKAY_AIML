from fastapi import FastAPI, File, UploadFile
from transformers import pipeline
from PIL import Image
import requests
import io

from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

# Fetch your API key safely
USDA_API_KEY = os.getenv("MY_API_KEY")  # Use the value from .env

# Optional: test if it's loaded correctly
if USDA_API_KEY:
    print("API Key loaded successfully!")
else:
    print("API Key not found. Check your .env file.")

app = FastAPI(title="NutriScan Model API")

# Load SAME model (no change)
classifier = pipeline("image-classification", model="nateraw/food")

def get_usda_nutrition(food_name):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": food_name,
        "pageSize": 1,
        "api_key": USDA_API_KEY
    }

    response = requests.get(url, params=params).json()
    if "foods" not in response or len(response["foods"]) == 0:
        return None

    nutrients = response["foods"][0]["foodNutrients"]

    def find(name):
        for n in nutrients:
            if name.lower() in n["nutrientName"].lower():
                return n.get("value", 0)
        return 0

    return {
        "calories": find("Energy"),
        "protein": find("Protein"),
        "carbs": find("Carbohydrate"),
        "fat": find("Total lipid")
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = classifier(image)
    top = results[0]

    nutrition = get_usda_nutrition(top["label"])

    return {
        "food": top["label"],
        "confidence": top["score"],
        "nutrition": nutrition
    }