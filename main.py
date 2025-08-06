import streamlit as st
import pandas as pd
import numpy as np
import openai
import os
import base64
import sqlite3
from datetime import datetime

# Initialize OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Database initialization
DB_NAME = "liteweight.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS weights(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weight REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            duration REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS foods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            calories REAL,
            date TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS water(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volume REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# call init_db
init_db()

# Insert functions
def insert_weight(weight: float, date: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO weights (weight, date) VALUES (?, ?)", (weight, date))
    conn.commit()
    conn.close()

def insert_activity(activity_type: str, duration: float, date: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO activities (type, duration, date) VALUES (?, ?, ?)", (activity_type, duration, date))
    conn.commit()
    conn.close()

def insert_food(description: str, calories: float, date: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO foods (description, calories, date) VALUES (?, ?, ?)", (description, calories, date))
    conn.commit()
    conn.close()

def insert_water(volume: float, date: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO water (volume, date) VALUES (?, ?)", (volume, date))
    conn.commit()
    conn.close()

# Fetch functions
def fetch_weights():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT weight, date FROM weights ORDER BY date ASC", conn)
    conn.close()
    return df

def fetch_activities():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT type, duration, date FROM activities", conn)
    conn.close()
    return df

def fetch_foods():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT description, calories, date FROM foods", conn)
    conn.close()
    return df

def fetch_water():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT volume, date FROM water", conn)
    conn.close()
    return df

# Streamlit UI
st.set_page_config(page_title="LiteWeight Streamlit", page_icon="🏋️", layout="centered")

st.title("LiteWeight – Streamlit Edition")
st.markdown("Log your health metrics and monitor your progress over time.")

tabs = st.tabs(["Weight Entry", "Activity Entry", "Food & Water", "Progress"])

# Weight Entry
with tabs[0]:
    st.header("Log Weight")
    weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1)
    weight_date = st.date_input("Date", value=datetime.today())
    if st.button("Add Weight Entry"):
        insert_weight(weight, weight_date.isoformat())
        st.success(f"Logged {weight} lbs on {weight_date}.")

# Activity Entry
with tabs[1]:
    st.header("Log Activity")
    activity_type = st.selectbox("Activity Type", ["Walk", "Run", "Bike", "Swim", "Workout"])
    duration = st.number_input("Duration (minutes)", min_value=0.0, step=1.0)
    activity_date = st.date_input("Date", value=datetime.today(), key="activity")
    if st.button("Add Activity Entry"):
        insert_activity(activity_type, duration, activity_date.isoformat())
        st.success(f"Logged {activity_type} for {duration} minutes on {activity_date}.")

# Food & Water
with tabs[2]:
    st.header("Food Analysis & Log")
    uploaded_file = st.file_uploader("Upload food photo", type=["png", "jpg", "jpeg"])
    manual_description = st.text_input("Food description (optional)")
    manual_calories = st.number_input("Calories (optional)", min_value=0.0, step=1.0)
    food_date = st.date_input("Date", value=datetime.today(), key="fooddate")
    if st.button("Analyze Photo"):
        if uploaded_file:
            image_bytes = uploaded_file.read()
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            system_prompt = ("You are a nutritionist AI analyzing photos of food for a fitness tracking app. "
                             "Given an image of food, provide a JSON object with the fields: "
                             "'description': a short description of the food, "
                             "'calories': your best guess of total calories as a number, "
                             "and 'confidence': a value between 0 and 1 indicating confidence in the calorie estimate. "
                             "If the image does not contain food, respond with description '', calories 0, and confidence 0.")
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [ {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"} } ] }
                    ],
                    max_tokens=400,
                )
                content = response["choices"][0]["message"]["content"]
                st.write("AI analysis result:")
                st.code(content)
                manual_description = manual_description or content
            except Exception as e:
                st.error(f"Failed to analyze image: {e}")
        else:
            st.warning("Please upload an image for analysis.")
    if st.button("Log Food"):
        desc = manual_description
        cals = manual_calories
        insert_food(desc, cals, food_date.isoformat())
        st.success("Food entry logged.")

    st.header("Log Water")
    water_volume = st.number_input("Water intake (fl oz)", min_value=0.0, step=1.0)
    water_date = st.date_input("Date", value=datetime.today(), key="waterdate")
    if st.button("Add Water Entry"):
        insert_water(water_volume, water_date.isoformat())
        st.success(f"Logged {water_volume} fl oz on {water_date}.")

# Progress Tab
with tabs[3]:
    st.header("Progress")
    weights_df = fetch_weights()
    if not weights_df.empty:
        weights_df["date"] = pd.to_datetime(weights_df["date"])
        weights_df = weights_df.sort_values("date")
        # For line chart, set date as index
        chart_df = weights_df.rename(columns={"date": "index"}).set_index("index")["weight"]
        st.line_chart(chart_df)
        start_weight = weights_df.iloc[0]["weight"]
        current_weight = weights_df.iloc[-1]["weight"]
        st.write(f"Start weight: {start_weight} lbs")
        st.write(f"Current weight: {current_weight} lbs")
        st.write(f"Difference: {current_weight - start_weight:+.2f} lbs")
    else:
        st.info("No weight entries found. Add some in the Weight tab.")

    # Activities summary
    acts_df = fetch_activities()
    if not acts_df.empty:
        total_minutes = acts_df["duration"].sum()
        st.subheader("Activity Summary")
        st.write(f"Total activities logged: {len(acts_df)}")
        st.write(f"Total minutes: {total_minutes}")
    # Food summary
    foods_df = fetch_foods()
    if not foods_df.empty:
        st.subheader("Food Summary")
        st.write(f"Total food entries: {len(foods_df)}")
        total_calories = foods_df["calories"].sum()
        st.write(f"Total calories: {total_calories}")
    # Water summary
    water_df = fetch_water()
    if not water_df.empty:
        st.subheader("Water Summary")
        st.write(f"Total water entries: {len(water_df)}")
        st.write(f"Total volume (fl oz): {water_df['volume'].sum()}")
