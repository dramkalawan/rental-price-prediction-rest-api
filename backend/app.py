# Import necessary libraries
import os
from pathlib import Path

import numpy as np
import joblib
import pandas as pd
from flask import Flask, request, jsonify

# Initialize the Flask application
rental_price_predictor_api = Flask("Airbnb Rental Price Predictor")

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "rental_price_prediction_model_v1_0.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# Load the trained machine learning model
model = joblib.load(MODEL_PATH)

REQUIRED_COLUMNS = [
    "room_type",
    "accommodates",
    "bathrooms",
    "cancellation_policy",
    "cleaning_fee",
    "instant_bookable",
    "review_scores_rating",
    "bedrooms",
    "beds",
]


@rental_price_predictor_api.get('/')
def home():
    """Return a welcome message for the API."""
    return "Welcome to the Airbnb Rental Price Prediction API!"


@rental_price_predictor_api.post('/v1/rental')
def predict_rental_price():
    """Predict the rent price for a single property."""
    property_data = request.get_json(silent=True)
    if not property_data:
        return jsonify({"error": "Request body must be a JSON object."}), 400

    missing = [column for column in REQUIRED_COLUMNS if column not in property_data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    sample = {key: property_data[key] for key in REQUIRED_COLUMNS}
    input_data = pd.DataFrame([sample])

    predicted_log_price = model.predict(input_data)[0]
    predicted_price = round(float(np.exp(predicted_log_price)), 2)

    return jsonify({"Predicted Price (in dollars)": predicted_price})


@rental_price_predictor_api.post('/v1/rentalbatch')
def predict_rental_price_batch():
    """Predict rental prices for a batch of properties from a CSV upload."""
    uploaded_file = request.files.get('file')
    if uploaded_file is None:
        return jsonify({"error": "No file uploaded. Please send a CSV file under the 'file' field."}), 400

    try:
        input_data = pd.read_csv(uploaded_file)
    except Exception as exc:
        return jsonify({"error": f"Could not read uploaded CSV: {exc}"}), 400

    missing_cols = [column for column in REQUIRED_COLUMNS if column not in input_data.columns]
    if missing_cols:
        return jsonify({"error": f"CSV missing required fields: {missing_cols}"}), 400

    predicted_log_prices = model.predict(input_data).tolist()
    predicted_prices = [round(float(np.exp(log_price)), 2) for log_price in predicted_log_prices]

    output = {}
    if 'id' in input_data.columns:
        property_ids = input_data['id'].tolist()
        output = dict(zip(property_ids, predicted_prices))
    else:
        output = {str(index): price for index, price in enumerate(predicted_prices)}

    return output


if __name__ == '__main__':
    rental_price_predictor_api.run(host="0.0.0.0", port=7860, debug=True)
