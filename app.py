import streamlit as st
from PIL import Image
from transformers import pipeline
import requests
import pandas as pd
from datetime import date
from fpdf import FPDF

# ================= CONFIG =================
USDA_API_KEY = "rNdHSEd66Lzh8l9yOGPNUaOrlAOpFtKQzqSsHuvr"
APP_NAME = "🥗 NutriScan"
# =========================================

st.set_page_config(page_title="NutriScan", layout="wide")

# ================= LOGIN SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ================= LOGIN FUNCTION =================
def login():
    st.title("🔐 Login to NutriScan")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

# BLOCK APP IF NOT LOGGED IN
if not st.session_state.logged_in:
    login()
    st.stop()

# ================= SIDEBAR NAVBAR =================
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Scan Food", "Download Report", "Logout"]
)

if menu == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out successfully")
    st.rerun()

# ================= MISSIONS =================
MISSIONS = {
    "Weight Loss": {"calories": 1800, "protein": 120, "carbs": 180, "fat": 50},
    "Weight Gain": {"calories": 2600, "protein": 150, "carbs": 300, "fat": 70},
    "Maintain Weight": {"calories": 2200, "protein": 130, "carbs": 240, "fat": 60},
}

# ================= SESSION STATE =================
if "mission" not in st.session_state:
    st.session_state.mission = None

if "daily" not in st.session_state:
    st.session_state.daily = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "date": str(date.today())
    }

# ================= MODEL =================
@st.cache_resource
def load_model():
    return pipeline("image-classification", model="nateraw/food")

classifier = load_model()

# ================= USDA =================
def get_usda_nutrition(food_name):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"query": food_name, "pageSize": 1, "api_key": USDA_API_KEY}
    response = requests.get(url, params=params).json()

    if "foods" not in response or len(response["foods"]) == 0:
        return None

    nutrients = response["foods"][0]["foodNutrients"]

    def find(name):
        for n in nutrients:
            if name.lower() in n["nutrientName"].lower():
                return n.get("value", 0)
        return 0

    return {
        "calories": find("Energy"),
        "protein": find("Protein"),
        "carbs": find("Carbohydrate"),
        "fat": find("Total lipid"),
    }

# ================= ALERT COLOR =================
def traffic_color(value, limit):
    ratio = value / limit
    if ratio <= 0.8:
        return "🟢"
    elif ratio <= 1.0:
        return "🟡"
    else:
        return "🔴"

# ================= SAFE TEXT FOR PDF =================
def safe_text(text):
    return str(text).encode("latin-1", "ignore").decode("latin-1")

# ================= MISSION-BASED SUGGESTIONS =================
def generate_suggestions(daily, targets, mission):
    suggestions = []

    # Calories
    if daily["calories"] < 0.9 * targets["calories"]:
        if mission == "Weight Gain":
            suggestions.append("💡 Eat more calories today to reach your goal (nuts, avocado, whole grains).")
        elif mission == "Weight Loss":
            suggestions.append("🟢 You are under your calorie target, keep it up!")
        else:
            suggestions.append("⚡ Keep your calorie intake balanced.")
    elif daily["calories"] > targets["calories"]:
        if mission == "Weight Loss":
            suggestions.append("⚠️ You have exceeded your calorie goal. Consider lighter meals next.")
        elif mission == "Weight Gain":
            suggestions.append("🟢 You are on track with your calorie intake.")
        else:
            suggestions.append("⚡ You are over your target slightly, adjust next meal.")

    # Protein
    if daily["protein"] < 0.8 * targets["protein"]:
        suggestions.append("💡 Increase protein intake (eggs, paneer, chicken, dal).")
    elif daily["protein"] > targets["protein"]:
        suggestions.append("✅ Protein intake is sufficient.")

    # Fat
    if daily["fat"] > targets["fat"]:
        suggestions.append("⚠️ Fat intake exceeded. Avoid fried foods.")

    # Carbs
    if daily["carbs"] < 0.8 * targets["carbs"]:
        suggestions.append("💡 Eat some complex carbs (brown rice, oats, whole wheat bread).")
    elif daily["carbs"] > targets["carbs"]:
        suggestions.append("⚠️ Carbs intake exceeded, try to limit sugary foods.")

    if not suggestions:
        suggestions.append("🟢 Great balance today! Keep it up.")

    return suggestions

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("🥗 NutriScan – Fitness Mission Tracker")
    st.caption("Scan food • Track macros • Stay fit")
    st.subheader(f"👋 Hey, {st.session_state.username}")

    st.subheader("🎯 Select Your Fitness Mission")
    mission = st.selectbox("Choose your goal:", list(MISSIONS.keys()))
    st.session_state.mission = mission
    targets = MISSIONS[mission]

    st.success(f"Mission Selected: **{mission}**")

    suggestions = generate_suggestions(st.session_state.daily, targets, mission)
    st.subheader("🤖 Smart Suggestions")
    for s in suggestions:
        st.write(s)

# ================= SCAN FOOD =================
# ================= SCAN FOOD =================
if menu == "Scan Food":
    st.title("📸 Scan Food")
    image_file = st.file_uploader("Upload food image", ["jpg", "png", "jpeg"])

    if image_file:
        image = Image.open(image_file).convert("RGB")
        st.image(image, width=300)

        with st.spinner("Detecting food..."):
            results = classifier(image)

        food = results[0]["label"]
        st.info(f"Detected Food: **{food}**")

        if st.button("Add Meal"):
            nutrition = get_usda_nutrition(food)
            if nutrition:
                for k in ["calories", "protein", "carbs", "fat"]:
                    st.session_state.daily[k] += nutrition[k]
                st.success("Meal added to today’s intake ✔")
            else:
                st.warning(f"No nutrition info found for '{food}'")

    st.divider()
    st.subheader("📊 Today’s Nutrition Summary")

    metrics = ["calories", "protein", "carbs", "fat"]
    targets = MISSIONS[st.session_state.mission]

    # Metric cards
    cols = st.columns(4)
    for i, m in enumerate(metrics):
        cols[i].metric(
            f"{m.capitalize()} {traffic_color(st.session_state.daily[m], targets[m])}",
            f"{st.session_state.daily[m]:.1f}",
            f"/ {targets[m]}"
        )

    # Bar chart for visualization
    st.subheader("📈 Progress Chart")
    df = pd.DataFrame({
        "Consumed": [st.session_state.daily[m] for m in metrics],
        "Target": [targets[m] for m in metrics]
    }, index=[m.capitalize() for m in metrics])
    st.bar_chart(df)

    # Smart suggestions
    suggestions = generate_suggestions(st.session_state.daily, targets, st.session_state.mission)
    st.subheader("🤖 Smart Suggestions")
    for s in suggestions:
        st.write(s)
# ================= PDF DOWNLOAD =================
if menu == "Download Report":
    st.subheader("📄 Download Daily Report")

    suggestions = generate_suggestions(st.session_state.daily, MISSIONS[st.session_state.mission], st.session_state.mission)
    metrics = ["calories", "protein", "carbs", "fat"]
    targets = MISSIONS[st.session_state.mission]

    def generate_pdf():
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, safe_text("NutriScan : Daily Nutrition Report"), ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, safe_text(f"User: {st.session_state.username}"), ln=True)
        pdf.cell(0, 8, safe_text(f"Mission: {st.session_state.mission}"), ln=True)
        pdf.cell(0, 8, safe_text(f"Date: {st.session_state.daily['date']}"), ln=True)
        pdf.ln(5)

        for m in metrics:
            pdf.cell(0, 8, safe_text(f"{m}: {st.session_state.daily[m]:.1f} / {targets[m]}"), ln=True)

        pdf.ln(5)
        for s in suggestions:
            pdf.multi_cell(0, 8, safe_text(s))

        return pdf.output(dest="S").encode("latin-1")

    if st.button("Generate PDF"):
        pdf_bytes = generate_pdf()
        st.download_button(
            "Download PDF",
            pdf_bytes,
            f"NutriScan_Report_{st.session_state.daily['date']}.pdf",
            "application/pdf"
        )