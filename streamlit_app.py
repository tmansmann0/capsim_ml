import streamlit as st
import pandas as pd
import joblib
import pyperclip

# Load the trained model (Make sure the model file is in the same directory or provide the correct path)
model = joblib.load('capsim_round_prediction_model_0_to_5.pkl')

# Dummy predictive function using the trained model
def predict_next_round(input_data):
    predictions = model.predict(input_data)
    return predictions

# Rule-based Ideal Position calculation
def ideal_position_rule(performance_r2, performance_r1, size_r2, size_r1):
    performance_modifier = performance_r2 - performance_r1
    size_modifier = size_r2 - size_r1
    next_performance = performance_r2 + performance_modifier
    next_size = size_r2 + size_modifier
    return next_performance, next_size

# Copy CSV to clipboard function
def copy_to_clipboard(dataframe):
    csv_data = dataframe.to_csv(index=False)
    pyperclip.copy(csv_data)

# Streamlit app setup
st.title("Capsim Round Prediction")

# Allow users to input data for two rounds
st.header("Input Round Information")
round_1 = st.text_input("Enter Round 1 Data (comma-separated, format: age, price lower, price upper, MTBF lower, MTBF upper, performance, size)")
round_2 = st.text_input("Enter Round 2 Data (same format as above)")

# Parse the input data
if round_1 and round_2:
    round_1_data = list(map(float, round_1.split(',')))
    round_2_data = list(map(float, round_2.split(',')))

    # Prepare data for the model (simply using round number as an example)
    input_data = pd.DataFrame({
        'round': [3],  # Predict for round 3
        'segment_size': [1],  # Assuming we're working with the 'size' segment, adjust as necessary
        # Add more feature data based on the segment
    })

    # Predict next round using the model
    model_predictions = predict_next_round(input_data)

    # Predict next round using rule-based Ideal Position
    performance_next, size_next = ideal_position_rule(round_2_data[5], round_1_data[5], round_2_data[6], round_1_data[6])

    # Create a DataFrame to display the predicted next round data
    next_round_data = {
        "age expectation": [model_predictions[0][0]],
        "price lower expectation": [model_predictions[0][1]],
        "price upper expectation": [model_predictions[0][2]],
        "MTBF lower limit": [model_predictions[0][3]],
        "MTBF upper limit": [model_predictions[0][4]],
        "Ideal Position PMFT": [performance_next],
        "Ideal Position Size": [size_next]
    }
    next_round_df = pd.DataFrame(next_round_data)

    # Display the predicted data
    st.subheader("Predicted Next Round Data")
    st.dataframe(next_round_df)

    # Copy button to copy CSV-formatted data
    if st.button("Copy CSV Data"):
        copy_to_clipboard(next_round_df)
        st.success("CSV data copied to clipboard!")

# Instructions for how to use the app
st.write("""
Instructions:
1. Enter the data for two rounds using the format: age, price lower, price upper, MTBF lower, MTBF upper, performance, size.
2. Click the "Copy CSV Data" button to copy the predicted next round data in CSV format.
""")
