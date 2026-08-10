#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import streamlit as st
import joblib
from PIL import Image
from sklearn.preprocessing import StandardScaler
from database import (
    create_tables,
    save_prediction,
    get_prediction_history,
    delete_prediction,
    get_prediction_stats,
    get_prediction_chart_data
)
from auth import register, login, logout

create_tables()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

st.set_page_config(
    page_title="Car Price Prediction App",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="auto"
)


@st.cache_resource
def load(scaler_path, ohe_path, model_path):
    sc = joblib.load(scaler_path)
    ohe = joblib.load(ohe_path)
    model = joblib.load(model_path)
    return sc, ohe, model


def inference(row, cols, scaler, ohe, model):

    df = pd.DataFrame([row], columns=cols)

    # Numerical columns
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    car_num_cols = list(df.select_dtypes(include=numerics).columns)
    df[car_num_cols] = scaler.transform(df[car_num_cols])

    # Categorical columns
    car_cat_cols = list(df.select_dtypes(exclude=numerics).columns)

    # One Hot Encoding
    car_ohe = ohe.transform(df[car_cat_cols])

    if hasattr(car_ohe, "toarray"):
        car_ohe = car_ohe.toarray()

    car_df_ohe = pd.DataFrame(
        car_ohe,
        columns=ohe.get_feature_names_out(car_cat_cols)
    )

    df = df.drop(columns=car_cat_cols)
    df = pd.concat([df.reset_index(drop=True), car_df_ohe], axis=1)

    price = model.predict(df)[0]

    return price

def login_page():

    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Invalid username or password.")


def register_page():

    st.title("Register")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):

        if password != confirm_password:
            st.error("Passwords do not match.")

        else:
            success = register(username, email, password)

            if success:
                st.success("Registration successful. Please login.")
            else:
                st.error("Username or email already exists.")
                

# Show login/register page if user is not logged in
if not st.session_state.logged_in:

    page = st.sidebar.selectbox(
        "Account",
        ["Login", "Register"]
    )

    if page == "Login":
        login_page()
    else:
        register_page()

    st.stop()
    
# ------------------------
st.sidebar.write(f"Logged in as: {st.session_state.username}")

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Car Price Prediction", "Prediction History"]
)

if st.sidebar.button("Logout"):
    logout()
    st.rerun()

if page == "Dashboard":

    st.title("Dashboard")

    stats = get_prediction_stats(st.session_state.user_id)

    total_predictions = stats["total_predictions"]
    average_price = stats["average_price"]
    highest_price = stats["highest_price"]
    lowest_price = stats["lowest_price"]

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Predictions",
            total_predictions
        )

    with col2:
        st.metric(
            "Average Price",
            f"${average_price:,.2f}" if average_price is not None else "$0.00"
        )

    col3, col4 = st.columns(2)

    with col3:
        st.metric(
            "Highest Price",
            f"${highest_price:,.2f}" if highest_price is not None else "$0.00"
        )

    with col4:
        st.metric(
            "Lowest Price",
            f"${lowest_price:,.2f}" if lowest_price is not None else "$0.00"
        )
        
    # //////////
    st.subheader("Prediction Price History")

    chart_data = get_prediction_chart_data(
        st.session_state.user_id
    )

    if chart_data:

        chart_df = pd.DataFrame(
            chart_data,
            columns=["Prediction Date", "Predicted Price"]
        )

        chart_df["Prediction Date"] = pd.to_datetime(
            chart_df["Prediction Date"]
        )

        chart_df = chart_df.set_index("Prediction Date")

        st.line_chart(chart_df["Predicted Price"])

    else:
        st.info("No prediction data available for the chart.")
# //////////
    st.stop()
    

if page == "Prediction History":

    st.title("Prediction History")

    history = get_prediction_history(st.session_state.user_id)

    if history:
        history_df = pd.DataFrame(history)

        history_df.columns = [
            "ID",
            "User ID",
            "Fuel Type",
            "Aspiration",
            "Door Number",
            "Car Body",
            "Drive Wheel",
            "Engine Location",
            "Wheel Base",
            "Car Length",
            "Car Width",
            "Car Height",
            "Curb Weight",
            "Engine Type",
            "Cylinder Number",
            "Engine Size",
            "Fuel System",
            "Bore Ratio",
            "Stroke",
            "Compression Ratio",
            "Horsepower",
            "Peak RPM",
            "City MPG",
            "Highway MPG",
            "Predicted Price",
            "Prediction Date"
        ]

        # Format date
        history_df["Prediction Date"] = pd.to_datetime(
            history_df["Prediction Date"]
        ).dt.strftime("%d-%m-%Y %I:%M %p")

        # Format price
        history_df["Predicted Price"] = history_df["Predicted Price"].apply(
            lambda x: f"${float(x.decode() if isinstance(x, bytes) else x):,.2f}"
        )

        # Columns displayed to the user
        display_df = history_df[
            [
                "ID",
                "Prediction Date",
                "Fuel Type",
                "Aspiration",
                "Car Body",
                "Drive Wheel",
                "Engine Type",
                "Engine Size",
                "Horsepower",
                "City MPG",
                "Highway MPG",
                "Predicted Price"
            ]
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Delete prediction
        st.subheader("Delete Prediction")

        prediction_id = st.selectbox(
            "Select Prediction ID to Delete",
            history_df["ID"].tolist()
        )

        if st.button("Delete Selected Prediction"):

            delete_prediction(
                prediction_id,
                st.session_state.user_id
            )

            st.success("Prediction deleted successfully.")
            st.rerun()

    else:
        st.info("No prediction history found.")

    st.stop()

st.title("Car Price Prediction App")
st.write("Predicting Price of a Car based on its features")

image = Image.open("data/car.jpg")
st.image(image, width="stretch")

st.write(
    "Please fill in the details of the car under consideration in the left sidebar and click on the button below!"
)

fuel_type = st.sidebar.selectbox("Fuel Type", ("diesel", "gas"))
aspiration = st.sidebar.selectbox("Aspiration", ("std", "turbo"))
door_number = st.sidebar.selectbox("Door Number", ("two", "four"))
car_body = st.sidebar.selectbox(
    "Car Body",
    ("convertible", "hardtop", "hatchback", "sedan", "wagon")
)
drive_wheel = st.sidebar.selectbox("Drive Wheel", ("rwd", "fwd", "4wd"))
engine_location = st.sidebar.selectbox("Engine Location", ("front", "rear"))

wheelbase = st.sidebar.number_input("Wheel Base", 0.0, 130.0, 86.6, 1.0)
carlength = st.sidebar.number_input("Car Length", 0.0, 210.0, 141.1, 1.0)
carwidth = st.sidebar.number_input("Car Width", 0.0, 75.0, 60.3, 1.0)
carheight = st.sidebar.number_input("Car Height", 0.0, 60.0, 47.8, 1.0)
curbweight = st.sidebar.number_input("Curb Weight", 0, 4070, 1488, 100)

engine_type = st.sidebar.selectbox(
    "Engine Type",
    ("dohc", "dohcv", "l", "ohc", "ohcf", "ohcv", "rotor")
)

cylinder_number = st.sidebar.selectbox(
    "Cylinder Number",
    ("two", "three", "four", "five", "six", "eight", "twelve")
)

enginesize = st.sidebar.number_input("Engine Size", 0.0, 330.0, 61.0, 10.0)

fuel_system = st.sidebar.selectbox(
    "Fuel System",
    ("1bbl", "2bbl", "4bbl", "idi", "mfi", "mpfi", "spdi", "spfi")
)

boreratio = st.sidebar.number_input("Bore Ratio", 0.0, 4.0, 2.54, 0.1)
stroke = st.sidebar.number_input("Stroke", 0.0, 4.5, 2.07, 0.1)
compression_ratio = st.sidebar.number_input("Compression Ratio", 0.0, 23.0, 7.0, 0.5)

horsepower = st.sidebar.slider("Horsepower", 0, 300, 48, 1)
peakrpm = st.sidebar.slider("Peak RPM", 0, 6600, 4150, 1)
citympg = st.sidebar.slider("City MPG", 0, 49, 13, 1)
highwaympg = st.sidebar.slider("Highway MPG", 0, 54, 16, 1)

row = [
    fuel_type,
    aspiration,
    door_number,
    car_body,
    drive_wheel,
    engine_location,
    wheelbase,
    carlength,
    carwidth,
    carheight,
    curbweight,
    engine_type,
    cylinder_number,
    enginesize,
    fuel_system,
    boreratio,
    stroke,
    compression_ratio,
    horsepower,
    peakrpm,
    citympg,
    highwaympg
]

cols = [
    'fueltype',
    'aspiration',
    'doornumber',
    'carbody',
    'drivewheel',
    'enginelocation',
    'wheelbase',
    'carlength',
    'carwidth',
    'carheight',
    'curbweight',
    'enginetype',
    'cylindernumber',
    'enginesize',
    'fuelsystem',
    'boreratio',
    'stroke',
    'compressionratio',
    'horsepower',
    'peakrpm',
    'citympg',
    'highwaympg'
]

if st.button("Predict Car Price"):
    sc, ohe, model = load(
        "models/scaler.joblib",
        "models/ohe.joblib",
        "models/XGBoost.joblib"
    )

    result = inference(row, cols, sc, ohe, model)

    st.success(f"Predicted Car Price: ${result:,.2f}")
    
    save_prediction(
        st.session_state.user_id,
        fuel_type,
        aspiration,
        door_number,
        car_body,
        drive_wheel,
        engine_location,
        wheelbase,
        carlength,
        carwidth,
        carheight,
        curbweight,
        engine_type,
        cylinder_number,
        enginesize,
        fuel_system,
        boreratio,
        stroke,
        compression_ratio,
        horsepower,
        peakrpm,
        citympg,
        highwaympg,
        result
    )
    