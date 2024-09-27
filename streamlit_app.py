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
st.header("Input Round 1 Information")
age_1 = st.number_input("Age Expectation (Round 1)", step=0.1)
price_lower_1 = st.number_input("Price Lower Expectation (Round 1)", step=0.1)
price_upper_1 = st.number_input("Price Upper Expectation (Round 1)", step=0.1)
mtbf_lower_1 = st.number_input("MTBF Lower Limit (Round 1)", step=100.0)
mtbf_upper_1 = st.number_input("MTBF Upper Limit (Round 1)", step=100.0)
performance_1 = st.number_input("Performance (Round 1)", step=0.1)
size_1 = st.number_input("Size (Round 1)", step=0.1)

st.header("Input Round 2 Information")
age_2 = st.number_input("Age Expectation (Round 2)", step=0.1)
price_lower_2 = st.number_input("Price Lower Expectation (Round 2)", step=0.1)
price_upper_2 = st.number_input("Price Upper Expectation (Round 2)", step=0.1)
mtbf_lower_2 = st.number_input("MTBF Lower Limit (Round 2)", step=100.0)
mtbf_upper_2 = st.number_input("MTBF Upper Limit (Round 2)", step=100.0)
performance_2 = st.number_input("Performance (Round 2)", step=0.1)
size_2 = st.number_input("Size (Round 2)", step=0.1)

# Predict next round based on input
if st.button("Predict Round 3 Data"):
    # Predict next round using rule-based Ideal Position
    performance_next, size_next = ideal_position_rule(performance_2, performance_1, size_2, size_1)

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
1. Enter the data for two rounds using the fields for age, price, MTBF, performance, and size.
2. Click "Predict Round 3 Data" to see the prediction.
3. Download the predicted next round data as a CSV.
""")
