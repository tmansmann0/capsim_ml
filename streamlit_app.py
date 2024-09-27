import streamlit as st
import pandas as pd
import joblib

# Load the trained model
@st.cache(allow_output_mutation=True)
def load_model():
    model = joblib.load("capsim_round_prediction_model_0_to_5.pkl")
    return model

model = load_model()

# Rule-based Ideal Position calculation
def ideal_position_rule(performance_r2, performance_r1, size_r2, size_r1):
    performance_modifier = performance_r2 - performance_r1
    size_modifier = size_r2 - size_r1
    next_performance = performance_r2 + performance_modifier
    next_size = size_r2 + size_modifier
    return next_performance, next_size

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

    # Predict next round using rule-based Ideal Position
    performance_next, size_next = ideal_position_rule(round_2_data[5], round_1_data[5], round_2_data[6], round_1_data[6])

    # Prepare input for the predictive model
    test_df = pd.DataFrame({
        'round': [5],
        'segment_size': [1]  # Assuming 'size' category is being used
    })

    # Use the model to predict the other variables for round 5
    X_test = pd.get_dummies(test_df, drop_first=True)
    predictions = model.predict(X_test)

    # Create a DataFrame to display the predicted next round data
    next_round_data = {
        "age expectation": [predictions[0][0]],
        "price lower expectation": [predictions[0][1]],
        "price upper expectation": [predictions[0][2]],
        "MTBF lower limit": [predictions[0][3]],
        "MTBF upper limit": [predictions[0][4]],
        "Ideal Position PMFT": [performance_next],
        "Ideal Position Size": [size_next]
    }
    next_round_df = pd.DataFrame(next_round_data)

    # Display the predicted data
    st.subheader("Predicted Next Round Data")
    st.dataframe(next_round_df)

    # Copy button to copy CSV-formatted data
    csv_data = next_round_df.to_csv(index=False)
    st.download_button("Download CSV", csv_data, "predicted_round_5.csv")

# Instructions for how to use the app
st.write("""
Instructions:
1. Enter the data for two rounds using the format: age, price lower, price upper, MTBF lower, MTBF upper, performance, size.
2. Click the "Download CSV" button to save the predicted next round data.
""")
