from flask import Flask, render_template, request, jsonify
from utils import predict_rent
import pickle
import pandas as pd

app = Flask(__name__)

# LOAD DATA

df = pd.read_csv("datasets/fullcleaned_house_data.csv")

cities = sorted(df["city"].dropna().unique())
furnishings = sorted(df["furnishing"].dropna().unique())

# City → Locality mapping
city_locality_map = {}
for city in cities:
    city_locality_map[city] = sorted(
        df[df["city"] == city]["locality"].dropna().unique()
    )

# NEW: City + BHK MEDIAN
city_bhk_median = df.groupby(['city', 'beds'])['rent'].median().to_dict()


# HOME PAGE

@app.route("/")
def home():
    return render_template(
        "index.html",
        cities=cities,
        furnishings=furnishings,
        city_locality_map=city_locality_map
    )

# RESULT PAGE

@app.route("/result")
def result():
    return render_template("result.html")


# PREDICT API

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

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
            "house_type": f'{int(data["beds"])} BHK Flat'
        }

        if (
            input_data["area"] <= 0 or
            input_data["beds"] <= 0 or
            input_data["bathrooms"] <= 0 or
            input_data["balconies"] < 0
        ):
            return jsonify({"success": False, "error": "Please enter valid numeric values."}), 400

        # Prediction
        prediction = predict_rent(input_data)
        predicted_rent = int(round(prediction))

        city = input_data["city"]
        beds = input_data["beds"]

        #  MEDIAN RENT
        median_rent = city_bhk_median.get((city, beds), None)

        # fallback (important)
        if median_rent is None:
            median_rent = int(df["rent"].median())
        else:
            median_rent = int(median_rent)

        # % DIFFERENCE
        percent_diff = ((predicted_rent - median_rent) / median_rent) * 100
        percent_diff = round(percent_diff, 1)

        #  PRICE LEVEL
        if percent_diff < -15:
            price_level = "Cheap"
        elif percent_diff <= 15:
            price_level = "Moderate"
        else:
            price_level = "Expensive"

        return jsonify({
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
            "furnishing": input_data["furnishing"]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# RUN

if __name__ == "__main__":
    app.run(debug=True)
