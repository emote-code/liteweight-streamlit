import streamlit as st
import pandas as pd
import numpy as np
import openai
import os
import base64
import sqlite3
from datetime import datetime, date

# Initialize OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS fastings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duration REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS exercises(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Insert functions
def insert_weight(weight, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO weights (weight, date) VALUES (?, ?)", (weight, date_str))
    conn.commit()
    conn.close()

def insert_activity(activity_type, duration, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO activities (type, duration, date) VALUES (?, ?, ?)", (activity_type, duration, date_str))
    conn.commit()
    conn.close()

def insert_food(desc, calories, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO foods (description, calories, date) VALUES (?, ?, ?)", (desc, calories, date_str))
    conn.commit()
    conn.close()

def insert_water(volume, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO water (volume, date) VALUES (?, ?)", (volume, date_str))
    conn.commit()
    conn.close()

def insert_fasting(duration, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO fastings (duration, date) VALUES (?, ?)", (duration, date_str))
    conn.commit()
    conn.close()

def insert_exercise(routine, date_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO exercises (routine, date) VALUES (?, ?)", (routine, date_str))
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

def fetch_fastings():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT duration, date FROM fastings", conn)
    conn.close()
    return df

def fetch_exercises():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT routine, date FROM exercises", conn)
    conn.close()
    return df

# Helper function for AI food analysis
def analyze_food_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    system_prompt = ("You are a nutritionist AI analyzing photos of food for a fitness tracking app. "
                     "Given an image of food, provide a JSON object with the fields: "
                     "'description': a short description of the food, "
                     "'calories': your best guess of total calories as a number, "
                     "and 'confidence': a value between 0 and 1 indicating confidence in the calorie estimate. "
                     "If the image does not contain food, respond with description '', calories 0, and confidence 0.")
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [ {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"} } ] }
        ],
        max_tokens=400,
    )
    return response["choices"][0]["message"]["content"]

# UI configuration
st.set_page_config(page_title="LiteWeight", page_icon="🏋️", layout="centered")

tabs = st.tabs(["Activity", "Consumption", "Progress"])
today = date.today()
selected_date = st.date_input("Select Date", value=today, key="selected_date")

# Activity Tab
with tabs[0]:
    st.header(selected_date.strftime("%A, %B %d"))
    # Weight Section
    st.subheader("Weight")
    weight_df = fetch_weights()
    last_weight = weight_df["weight"].iloc[-1] if not weight_df.empty else None
    st.text_input("Last weight (lbs)", value=str(last_weight) if last_weight else "No previous entry", disabled=True)
    weight_value = st.number_input("Weight (lbs)", min_value=0.0, step=0.1, key="weight_input")
    if st.button("Log Weight"):
        insert_weight(weight_value, selected_date.isoformat())
        st.success(f"Logged weight {weight_value} lbs on {selected_date}")
    st.divider()

    # Walk/Run Section
    st.subheader("Walk/Run")
    act_type = st.radio("Type", ["Walk", "Run"], horizontal=True, key="act_type")
    act_duration = st.number_input("Duration (minutes)", min_value=0.0, step=1.0, key="act_duration")
    if st.button("Log Activity"):
        insert_activity(act_type, act_duration, selected_date.isoformat())
        st.success(f"Logged {act_type} for {act_duration} minutes on {selected_date}")
    st.divider()

    # Fasting Section
    st.subheader("Fasting")
    fasting_hours = st.number_input("Hours", min_value=0.0, step=1.0, key="fasting_hours")
    if st.button("Log Fasting"):
        insert_fasting(fasting_hours, selected_date.isoformat())
        st.success(f"Logged fasting session of {fasting_hours} hours on {selected_date}")
    st.divider()

    # Exercise Section
    st.subheader("Exercise")
    routines = ["Upper Body", "Lower Body", "Full Body", "Cardio"]
    exercise_routine = st.selectbox("Choose routine", routines, key="exercise_routine")
    if st.button("Log Exercise Done"):
        insert_exercise(exercise_routine, selected_date.isoformat())
        st.success(f"Logged exercise routine: {exercise_routine} on {selected_date}")

# Consumption Tab
with tabs[1]:
    st.header("Consumption")
    # Food Section
    st.subheader("Food Analysis & Log")
    food_file = st.file_uploader("Upload food photo", type=["png", "jpg", "jpeg"], key="food_file")
    manual_desc = st.text_input("Description (optional)", key="manual_desc")
    manual_cal = st.number_input("Calories (optional)", min_value=0.0, step=1.0, key="manual_cal")
    if st.button("Analyze Photo"):
        if food_file:
            try:
                content = analyze_food_image(food_file.read())
                st.write("AI analysis result:")
                st.code(content)
                if manual_desc == "":
                    manual_desc = content
            except Exception as e:
                st.error(f"Failed to analyze image: {e}")
        else:
            st.warning("Please upload an image.")
    if st.button("Log Food"):
        insert_food(manual_desc, manual_cal, selected_date.isoformat())
        st.success("Food entry logged.")
    st.divider()

    # Water Section
    st.subheader("Water")
    water_vol = st.number_input("Water intake (fl oz)", min_value=0.0, step=1.0, key="water_vol_input")
    if st.button("Log Water"):
        insert_water(water_vol, selected_date.isoformat())
        st.success(f"Logged water intake of {water_vol} fl oz on {selected_date}")

# Progress Tab
with tabs[2]:
    st.header("Progress Overview")
    # Weight Chart
    weights_df = fetch_weights()
    if not weights_df.empty:
        weights_df["date"] = pd.to_datetime(weights_df["date"])
        weights_df = weights_df.sort_values("date")
        chart_df = weights_df.rename(columns={"date": "index"}).set_index("index")["weight"]
        st.line_chart(chart_df)
        start_w = weights_df.iloc[0]["weight"]
        current_w = weights_df.iloc[-1]["weight"]
        st.write(f"Start weight: {start_w} lbs")
        st.write(f"Current weight: {current_w} lbs")
        st.write(f"Difference: {current_w - start_w:+.2f} lbs")
    else:
        st.info("No weight entries yet.")

    # Activity Summary
    acts = fetch_activities()
    if not acts.empty:
        total_minutes = acts["duration"].sum()
        st.subheader("Activity Summary")
        st.write(f"Total activities: {len(acts)}")
        st.write(f"Total minutes: {total_minutes}")

    # Food Summary
    foods = fetch_foods()
    if not foods.empty:
        st.subheader("Food Summary")
        st.write(f"Entries: {len(foods)}")
        st.write(f"Total calories: {foods['calories'].sum()}")

    # Water Summary
    water_df = fetch_water()
    if not water_df.empty:
        st.subheader("Water Summary")
        st.write(f"Entries: {len(water_df)}")
        st.write(f"Total volume (fl oz): {water_df['volume'].sum()}")

    # Fasting Summary
    fasts = fetch_fastings()
    if not fasts.empty:
        st.subheader("Fasting Summary")
        st.write(f"Sessions: {len(fasts)}")
        st.write(f"Total hours fasted: {fasts['duration'].sum()}")

    # Exercise Summary
    exs = fetch_exercises()
    if not exs.empty:
        st.subheader("Exercise Summary")
        st.write(f"Sessions: {len(exs)}")
        st.write("Routines logged:")
        st.write(exs["routine"].value_counts())
