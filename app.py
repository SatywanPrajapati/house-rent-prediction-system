from flask import Flask, render_template, request, jsonify
from utils import predict_rent
import pickle
import pandas as pd

app = Flask(__name__)

# ==============================
# LOAD DATA
# ==============================
df = pd.read_csv("datasets/fullcleaned_house_data.csv")

cities = sorted(df["city"].dropna().unique())
furnishings = sorted(df["furnishing"].dropna().unique())

# City → Locality mapping
city_locality_map = {}
for city in cities:
    city_locality_map[city] = sorted(
        df[df["city"] == city]["locality"].dropna().unique()
    )

city_mean = pickle.load(open("model/city_mean.pkl", "rb"))

# ==============================
# HOME PAGE
# ==============================
@app.route("/")
def home():
    return render_template(
        "index.html",
        cities=cities,
        furnishings=furnishings,
        city_locality_map=city_locality_map
    )

# ==============================
# RESULT PAGE
# ==============================
@app.route("/result")
def result():
    return render_template("result.html")

# ==============================
# PREDICT API
# ==============================
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

            # FIXED
            "house_type": f'{int(data["beds"])} BHK Flat'
        }

        # Validation
        if (
            input_data["area"] <= 0 or
            input_data["beds"] <= 0 or
            input_data["bathrooms"] <= 0 or
            input_data["balconies"] < 0
        ):
            return jsonify({"success": False, "error": "Invalid values"}), 400

        prediction = predict_rent(input_data)

        city_avg = city_mean.get(input_data["city"], None)

        if city_avg:
            if prediction > city_avg:
                price_level = "Above Average"
            elif prediction < city_avg:
                price_level = "Below Average"
            else:
                price_level = "Average"
        else:
            price_level = None

        return jsonify({
            "success": True,
            "prediction": round(prediction),
            "city": input_data["city"],
            "locality": input_data["locality"],
            "city_avg": round(city_avg) if city_avg else None,
            "price_level": price_level
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)