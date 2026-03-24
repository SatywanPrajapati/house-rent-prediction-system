import pickle
import numpy as np
import pandas as pd
import os

# =========================
# PATH SETUP
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load model files once so each prediction request stays lightweight.
model = pickle.load(open(os.path.join(BASE_DIR, "model/house_model.pkl"), "rb"))
city_mean = pickle.load(open(os.path.join(BASE_DIR, "model/city_mean.pkl"), "rb"))
locality_mean = pickle.load(open(os.path.join(BASE_DIR, "model/locality_mean.pkl"), "rb"))

# =========================
# ENCODING MAP
# =========================
FURNISHING_MAP = {
    "Unfurnished": 0,
    "Semi-Furnished": 1,
    "Furnished": 2
}

# =========================
# FEATURE PREPARATION
# =========================
def prepare_features(data):
    # Convert raw input into the numeric values expected by the model.
    area = float(data["area"])
    beds = int(data["beds"])
    bathrooms = float(data["bathrooms"])
    balconies = float(data["balconies"])

    city = data["city"]
    locality = data["locality"]
    furnishing = data["furnishing"]

    # Recreate the engineered features used while training the model.
    area_per_bed = area / (beds + 1)
    bath_per_bed = bathrooms / (beds + 1)
    total_rooms = beds + bathrooms
    beds_area = beds * area

    # Encode text fields into numeric values using precomputed averages.
    city_encoded = float(city_mean.get(city, city_mean.mean()))
    locality_encoded = float(locality_mean.get(locality, city_encoded))

    furnishing_encoded = FURNISHING_MAP.get(furnishing, 1)

    features = pd.DataFrame([{
        "area": area,
        "beds": beds,
        "bathrooms": bathrooms,
        "balconies": balconies,
        "area_per_bed": area_per_bed,
        "bath_per_bed": bath_per_bed,
        "total_rooms": total_rooms,
        "beds_area": beds_area,
        "locality_encoded": locality_encoded,
        "city_encoded": city_encoded,
        "furnishing_encoded": furnishing_encoded
    }])

    return features

# =========================
# PREDICTION
# =========================
def predict_price(data):
    # Build the final feature frame for prediction.
    features = prepare_features(data)

    pred_log = model.predict(features)

    # Convert the prediction back from log scale to the original rent scale.
    price = float(np.expm1(pred_log[0]))

    # Apply the same rent adjustment logic used in this project.
    beds = int(data["beds"])
    if beds == 2:
        price *= 0.95
    elif beds == 3:
        price *= 1.05
    elif beds >= 4:
        price *= 1.15

    return int(price)
