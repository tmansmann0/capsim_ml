import streamlit as st
import pandas as pd
import joblib
from pathlib import Path

# Set page configuration
st.set_page_config(page_title="Capsim Round Prediction", layout="centered")

# Load the trained model with caching
@st.cache_resource
def load_model():
    model_path = Path("capsim_round_prediction_model_0_to_5.pkl")
    if not model_path.is_file():
        st.error(f"Model file not found at {model_path.resolve()}")
        return None
    model = joblib.load(model_path)
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
st.title("📈 Capsim Round Prediction")

# Instructions for how to use the app
st.write("""
## Instructions:
1. **Input Data for Two Rounds:**
   - **Current Round:** Enter the data for the current round.
   - **Prior Round:** Enter the data from the previous round.
2. **Predict Next Round:**
   - Click the "Predict Next Round Data" button to generate predictions.
3. **Download Results:**
   - Use the "Download CSV" button to save the predicted data.
""")

# Function to collect input data
def get_input(round_label):
    with st.container():
        st.subheader(f"**Input {round_label} Round's Capsim Courier Info**")
        age = st.number_input(f"Age Expectation ({round_label} Round)", step=0.1, format="%.1f")
        price_lower = st.number_input(f"Price Lower Expectation ({round_label} Round)", step=0.1, format="%.1f")
        price_upper = st.number_input(f"Price Upper Expectation ({round_label} Round)", step=0.1, format="%.1f")
        mtbf_lower = st.number_input(f"MTBF Lower Limit ({round_label} Round)", step=100.0, format="%.1f")
        mtbf_upper = st.number_input(f"MTBF Upper Limit ({round_label} Round)", step=100.0, format="%.1f")
        performance = st.number_input(f"Performance ({round_label} Round)", step=0.1, format="%.1f")
        size = st.number_input(f"Size ({round_label} Round)", step=0.1, format="%.1f")
    return age, price_lower, price_upper, mtbf_lower, mtbf_upper, performance, size

# Input for the current round
age_2, price_lower_2, price_upper_2, mtbf_lower_2, mtbf_upper_2, performance_2, size_2 = get_input("Current")

# Input for the prior round
age_1, price_lower_1, price_upper_1, mtbf_lower_1, mtbf_upper_1, performance_1, size_1 = get_input("Prior")

# Predict next round based on input
if st.button("🔮 Predict Next Round Data"):
    if model is None:
        st.error("Model is not loaded. Please ensure the model file is available.")
    else:
        # Calculate Ideal Positions
        performance_next, size_next = ideal_position_rule(
            performance_r2=performance_2,
            performance_r1=performance_1,
            size_r2=size_2,
            size_r1=size_1
        )

        # Prepare input for the predictive model
        # Ensure that the features match what the model expects
        # Example: If the model expects more features, include them accordingly
        test_data = {
            'round': 5,  # Assuming round 5 is the target
            'segment_size': 1  # Adjust based on your model's training
            # Add other necessary features here
        }
        test_df = pd.DataFrame([test_data])

        # If your model requires categorical variables to be encoded, handle them here
        # For example, using get_dummies or other encoding methods
        # Ensure that the training and prediction feature sets align
        # Example:
        # X_test = pd.get_dummies(test_df, drop_first=True)
        X_test = test_df  # Modify as needed

        try:
            predictions = model.predict(X_test)
            # If predictions are multi-dimensional, adjust indexing
            # Example assumes predictions is 1D array
            if isinstance(predictions, (list, pd.Series)):
                predictions = [predictions]  # Convert to list of lists for consistency
            next_round_data = {
                "Age Expectation": [predictions[0][0]],
                "Price Lower Expectation": [predictions[0][1]],
                "Price Upper Expectation": [predictions[0][2]],
                "MTBF Lower Limit": [predictions[0][3]],
                "MTBF Upper Limit": [predictions[0][4]],
                "Ideal Position Performance": [performance_next],
                "Ideal Position Size": [size_next]
            }
            next_round_df = pd.DataFrame(next_round_data)

            # Display the predicted data
            st.subheader("📊 Predicted Next Round Data")
            st.dataframe(next_round_df)

            # Prepare CSV for download
            csv_data = next_round_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name="predicted_round.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"An error occurred during prediction: {e}")
