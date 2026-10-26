import streamlit as st
import pandas as pd
import requests
import os



def resolve_backend_url():
    configured = os.getenv("BACKEND_URL", "").strip()
    candidates = []
    if configured:
        candidates.append(configured.rstrip('/'))
    candidates.extend([
        "http://localhost:7860",
        "http://127.0.0.1:7860",
        "http://backend:7860",
        "http://bnb-backend:7860",
    ])

    for url in candidates:
        try:
            response = requests.get(f"{url}/", timeout=1)
            if response.status_code < 500:
                return url
        except requests.RequestException:
            continue
    return candidates[0] if candidates else "http://localhost:7860"


# Base URL of the Flask backend
BACKEND_URL = resolve_backend_url()

# Set the title of the Streamlit app
st.title("Airbnb Rental Price Prediction")

# Section for online prediction
st.subheader("Online Prediction")

# Collect user input for property features
room_type = st.selectbox("Room Type", ["Entire home/apt", "Private room", "Shared room"])
accommodates = st.number_input("Accommodates (Number of guests)", min_value=1, value=2)
bathrooms = st.number_input("Bathrooms", min_value=1, step=1, value=2)
cancellation_policy = st.selectbox("Cancellation Policy (kind of cancellation policy)", ["strict", "flexible", "moderate"])
cleaning_fee = st.selectbox("Cleaning Fee Charged?", ["True", "False"])
instant_bookable = st.selectbox("Instantly Bookable?", ["False", "True"])
review_scores_rating = st.number_input("Review Score Rating", min_value=0.0, max_value=100.0, step=1.0, value=90.0)
bedrooms = st.number_input("Bedrooms", min_value=0, step=1, value=1)
beds = st.number_input("Beds", min_value=0, step=1, value=1)

# Convert user input into a DataFrame
input_data = pd.DataFrame([{
    'room_type': room_type,
    'accommodates': accommodates,
    'bathrooms': bathrooms,
    'cancellation_policy': cancellation_policy,
    'cleaning_fee': cleaning_fee,
    'instant_bookable': 'f' if instant_bookable=="False" else "t",  # Convert to 't' or 'f'
    'review_scores_rating': review_scores_rating,
    'bedrooms': bedrooms,
    'beds': beds
}])

# Make prediction when the "Predict" button is clicked
if st.button("Predict", type="primary"):
    try:
        response = requests.post(
            f"{BACKEND_URL}/v1/rental",
            json=input_data.to_dict(orient='records')[0],
            timeout=10,
        )
        if response.status_code == 200:
            prediction = response.json()['Predicted Price (in dollars)']
            st.success(f"Predicted Rental Price (in dollars): {prediction}")
        else:
            st.error(f"Prediction API returned an error: {response.status_code}")
    except requests.RequestException as exc:
        st.error(f"Unable to connect to the prediction API at {BACKEND_URL}: {exc}")

# Section for batch prediction
st.subheader("Batch Prediction")

# Allow users to upload a CSV file for batch prediction
uploaded_file = st.file_uploader("Upload CSV file for batch prediction", type=["csv"])

# Make batch prediction when the "Predict Batch" button is clicked
if uploaded_file is not None:
    if st.button("Predict Batch", type="primary"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/v1/rentalbatch",
                files={"file": uploaded_file},
                timeout=20,
            )
            if response.status_code == 200:
                predictions = response.json()
                st.success("Batch predictions completed!")
                st.write(predictions)
            else:
                st.error(f"Batch prediction API returned an error: {response.status_code}")
        except requests.RequestException as exc:
            st.error(f"Unable to connect to the prediction API at {BACKEND_URL}: {exc}")
