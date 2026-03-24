from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from utils import predict_price, city_mean

# Create the Flask application instance.
app = Flask(__name__)

# =========================
# LOAD DATA FOR DROPDOWN
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATHS = [
    os.path.join(BASE_DIR, "datasets", "datasetindia_house_dataset.csv"),
    os.path.join(BASE_DIR, "Data", "Datasetindia_house_dataset.csv"),
    os.path.join(BASE_DIR, "data", "Datasetindia_house_dataset.csv"),
]

datasets_path = next((path for path in DATASET_PATHS if os.path.exists(path)), None)
if datasets_path is None:
    raise FileNotFoundError(
        "Dataset file not found in datasets/, Data/, or data/ directory."
    )

# Load the dataset once and prepare clean values for the form dropdowns.
df = pd.read_csv(datasets_path)
df.dropna(inplace=True)

df["city"] = df["city"].astype(str).str.strip()
df["locality"] = df["locality"].astype(str).str.strip()

cities = sorted(df["city"].unique())

city_locality_map = {
    city: sorted(df[df["city"] == city]["locality"].unique())
    for city in cities
}

furnishings = ["Unfurnished", "Semi-Furnished", "Furnished"]
REQUIRED_FIELDS = ("area", "beds", "bathrooms", "balconies", "city", "locality", "furnishing")


@app.context_processor
def inject_template_data():
    # Make the city-locality mapping available in templates globally.
    return {
        "city_locality_map": city_locality_map,
    }

# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    # Render the home page and send dropdown data to the form.
    return render_template(
        "index.html",
        cities=cities,
        city_locality_map=city_locality_map,
        furnishings=furnishings
    )

# =========================
# PREDICTION API
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    # Read JSON safely so invalid requests do not crash the app.
    data = request.get_json(silent=True) or {}

    # Ensure all required fields are present before calling the model.
    missing_fields = [field for field in REQUIRED_FIELDS if not str(data.get(field, "")).strip()]
    if missing_fields:
        return jsonify({
            "success": False,
            "error": f"Missing required fields: {', '.join(missing_fields)}",
        }), 400

    try:
        prediction = predict_price(data)
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({
            "success": False,
            "error": f"Invalid input: {exc}",
        }), 400

    city = str(data["city"]).strip()
    locality = str(data["locality"]).strip()

    # Compare the predicted rent with the average rent of the selected city.
    city_avg = float(city_mean.get(city, city_mean.mean()))
    if prediction > city_avg * 1.1:
        price_level = "Above Average"
    elif prediction < city_avg * 0.9:
        price_level = "Below Average"
    else:
        price_level = "Average"

    return jsonify({
        "success": True,
        "prediction": prediction,
        "city": city,
        "locality": locality,
        "benchmark_label": "City Average",
        "city_avg": int(city_avg),
        "price_level": price_level,
    })

# =========================
# RESULT PAGE
# =========================
@app.route("/result")
def result():
    # Read values from the query string after the frontend redirect.
    args = request.args.to_dict()

    city = args.get("city", "").strip()
    prediction = args.get("prediction", "0")

    try:
        prediction_value = float(prediction)
    except ValueError:
        prediction_value = 0.0

    # Reuse the same city benchmark logic used in the API.
    city_avg = float(city_mean.get(city, city_mean.mean()))
    if prediction_value > city_avg * 1.1:
        price_level = "Above Average"
    elif prediction_value < city_avg * 0.9:
        price_level = "Below Average"
    else:
        price_level = "Average"

    args.update({
        "benchmark_label": "City Average",
        "city_avg": int(city_avg),
        "price_level": price_level,
    })

    return render_template("result.html", **args)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
