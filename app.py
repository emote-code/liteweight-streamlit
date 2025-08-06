import streamlit as st
import pandas as pd
import numpy as np
import openai
import os
import base64

st.set_page_config(page_title="LiteWeight", page_icon=":weight_lifter:", layout="centered")

# Initialize OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("LiteWeight – Streamlit Edition")
st.markdown("Log your health metrics and monitor your progress.")

# Tabs for different entries and progress
tabs = st.tabs(["Weight Entry", "Activity Entry", "Food Analysis", "Progress"])

# Weight Entry Tab
with tabs[0]:
    st.header("Log Weight")
    weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1)
    weight_date = st.date_input("Date", key="weight_date")
    if st.button("Add Weight Entry"):
        # TODO: Insert into database
        st.success(f"Logged {weight} lbs on {weight_date}. (Database insertion not implemented)")

# Activity Entry Tab
with tabs[1]:
    st.header("Log Activity")
    activity_type = st.selectbox("Activity Type", ["Walk", "Run", "Bike", "Swim"])
    duration = st.number_input("Duration (minutes)", min_value=0, step=1)
    activity_date = st.date_input("Date", key="activity_date")
    if st.button("Add Activity Entry"):
        # TODO: Insert into database
        st.success(f"Logged {activity_type} for {duration} minutes on {activity_date}. (Database insertion not implemented)")

# Food Analysis Tab
with tabs[2]:
    st.header("Analyze Food & Log Entry")
    uploaded_file = st.file_uploader("Upload food image (PNG or JPG)", type=["png", "jpg", "jpeg"])
    manual_description = st.text_input("Food description (optional)")
    manual_calories = st.number_input("Calories (optional)", min_value=0, step=1)

    analysis_result = None
    if uploaded_file and st.button("Analyze Photo"):
        # Convert image to base64
        image_bytes = uploaded_file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        # Compose system prompt similar to Node implementation
        system_prompt = (
            "You are a nutritionist AI analyzing photos of food for a fitness tracking app. "
            "Given an image of food, provide a JSON response with three fields: "
            "`description` (a short description of the food), `calories` (your best guess of total calories as a number), "
            "and `confidence` (a value between 0 and 1 indicating your confidence in the calorie estimate). "
            "If the image does not contain food, respond with a description of what you see, approximate calories as 0, and confidence of 0."
        )
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/jpeg;base64," + base64_image
                                },
                            }
                        ],
                    },
                ],
                max_tokens=300,
            )
            content = response["choices"][0]["message"]["content"]
            st.write("AI analysis result:")
            st.code(content)
            analysis_result = content
        except Exception as e:
            st.error(f"Failed to analyze image: {e}")

    if st.button("Log Food Entry"):
        desc = manual_description
        cals = manual_calories
        if analysis_result:
            # Optionally combine manual description with AI result
            desc = desc or analysis_result
        # TODO: Insert into database
        st.success("Food entry logged. (Database insertion not implemented)")

# Progress Tab
with tabs[3]:
    st.header("Progress Overview")
    st.markdown("Below is a sample weight trend. Replace with real data from your database.")
    # Generate sample data for the past 30 days
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    weights = np.linspace(160, 150, num=30) + np.random.randn(30)
    df = pd.DataFrame({"Date": dates, "Weight": weights}).set_index("Date")
    st.line_chart(df)
