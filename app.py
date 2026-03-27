import os

import pandas as pd
from flask import Flask, jsonify, render_template, request

from utils import predict_rent

app = Flask(__name__)

# Load dataset and shared reference data.
df = pd.read_csv("datasets/fullcleaned_house_data.csv")
cities = sorted(df["city"].dropna().unique())
furnishings = sorted(df["furnishing"].dropna().unique())

city_locality_map = {
    city: sorted(df[df["city"] == city]["locality"].dropna().unique())
    for city in cities
}

city_bhk_median = df.groupby(["city", "beds"])["rent"].median().to_dict()

@app.route("/")
def home():
    return render_template(
        "index.html",
        cities=cities,
        furnishings=furnishings,
        city_locality_map=city_locality_map,
    )

@app.route("/result")
def result():
    return render_template("result.html")

@app.route("/localities/<city>")
def get_localities(city):
    localities = city_locality_map.get(city, [])
    return jsonify({"success": True, "localities": localities})

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"success": False, "error": "No input data"}), 400

        input_data = {
            "area": float(data["area"]),
            "beds": int(data["beds"]),
            "bathrooms": int(data["bathrooms"]),
            "balconies": int(data["balconies"]),
            "furnishing": data["furnishing"],
            "city": data["city"],
            "locality": data["locality"],
            "house_type": f'{int(data["beds"])} BHK Flat',
        }

        if (
            input_data["area"] <= 0
            or input_data["beds"] <= 0
            or input_data["bathrooms"] <= 0
            or input_data["balconies"] < 0
        ):
            return (
                jsonify(
                    {"success": False, "error": "Please enter valid numeric values."}
                ),
                400,
            )

        prediction = predict_rent(input_data)
        predicted_rent = int(round(prediction))

        city = input_data["city"]
        beds = input_data["beds"]
        median_rent = city_bhk_median.get((city, beds))
        median_rent = int(df["rent"].median()) if median_rent is None else int(median_rent)
        percent_diff = round(((predicted_rent - median_rent) / median_rent) * 100, 1)

        if percent_diff < -15:
            price_level = "Cheap"
        elif percent_diff <= 15:
            price_level = "Moderate"
        else:
            price_level = "Expensive"

        return jsonify(
            {
                "success": True,
                "rent": predicted_rent,
                "median_rent": median_rent,
                "percent_diff": percent_diff,
                "price_level": price_level,
                "city": city,
                "locality": input_data["locality"],
                "beds": beds,
                "bathrooms": input_data["bathrooms"],
                "balconies": input_data["balconies"],
                "area": input_data["area"],
                "furnishing": input_data["furnishing"],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
