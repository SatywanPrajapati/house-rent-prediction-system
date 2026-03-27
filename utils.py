import pickle
import numpy as np
import pandas as pd
import os

# LOAD MODEL FILES
model = pickle.load(open("model/house_model.pkl", "rb"))
encoders = pickle.load(open("model/encoders.pkl", "rb"))

# LOAD DATASET (for target encoding instead of pickle)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, "datasets/fullcleaned_house_data.csv")

df = pd.read_csv(data_path)

# CREATE ENCODING DICTIONARIES
locality_mean = df.groupby("locality")["rent"].mean().to_dict()
city_mean = df.groupby("city")["rent"].mean().to_dict()

# DEFAULT VALUES (safe fallback)
DEFAULT_LOCALITY = np.mean(list(locality_mean.values()))
DEFAULT_CITY = np.mean(list(city_mean.values()))

# SAFE ENCODER
def safe_encode(le, value):
    try:
        if value in le.classes_:
            return le.transform([value])[0]
        else:
            return 0
    except:
        return 0

# PREDICT FUNCTION
def predict_rent(data):

    # Feature Engineering
    total_rooms = data["beds"] + data["bathrooms"]
    area_log = np.log1p(data["area"])

    # Target Encoding
    locality_encoded = locality_mean.get(data["locality"], DEFAULT_LOCALITY)
    city_encoded = city_mean.get(data["city"], DEFAULT_CITY)

    # Safe Encoding
    furnishing = safe_encode(encoders["furnishing"], data["furnishing"])
    house_type = safe_encode(encoders["house_type"], data["house_type"])

    # Feature Order (IMPORTANT)
    features = np.array([
        data["beds"],
        data["bathrooms"],
        data["balconies"],
        furnishing,
        house_type,
        total_rooms,
        area_log,
        locality_encoded,
        city_encoded
    ]).reshape(1, -1)

    # MODEL PREDICTION
    log_prediction = model.predict(features)[0]
    final_prediction = np.expm1(log_prediction)

    # BHK ADJUSTMENT LOGIC ()
    bhk_factor = 1 + (0.05 * (data["beds"] - 1))
    final_prediction = final_prediction * bhk_factor

    return round(final_prediction, 2)

print("Model loaded successfully")