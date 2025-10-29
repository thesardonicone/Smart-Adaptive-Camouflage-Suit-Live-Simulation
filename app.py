import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime, UTC
import plotly.express as px
import io, qrcode

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Smart Adaptive Camouflage Suit",
    page_icon="🪖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        body { background-color: #0d1117; color: #ffffff; }
        .stApp { background-color: #0d1117; }
        .main-title { font-size: 28px; font-weight: bold; color: #00ffff; }
        .footer {
            text-align: center;
            padding: 20px;
            border-top: 1px solid #444;
            margin-top: 30px;
            color: #aaaaaa;
        }
        .repo-link {
            font-size: 16px;
            color: #00ffff;
            text-decoration: none;
            font-weight: bold;
        }
        .repo-link:hover {
            color: #00cccc;
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# INITIALISE STATE
# --------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "temp", "heart", "light", "mode"])

# --------------------------------------------------
# FUNCTIONS
# --------------------------------------------------
def predict_mode(temp, heart, light):
    if temp >= 40 or heart >= 160:
        return "Alert Mode"
    elif temp > 37 and light > 0.6:
        return "Heat Mode"
    elif temp < 30 and light < 0.4:
        return "Stealth Mode"
    else:
        return "Cool Mode"


def simulate_reading(preset, terrain, oxygen, radiation, space_mode):
    base_temp = random.uniform(31, 36)
    base_heart = random.randint(70, 90)
    base_light = random.uniform(0.3, 0.8)

    if preset == "Overheat":
        base_temp += random.uniform(6, 9)
        base_heart += random.randint(20, 40)
    elif preset == "High Exertion":
        base_temp += random.uniform(3, 6)
        base_heart += random.randint(40, 60)
    elif preset == "Low Light":
        base_light = random.uniform(0.1, 0.4)

    if space_mode:
        base_temp = random.uniform(22, 30)
        base_light = random.uniform(0.0, 0.3)

    if oxygen < 65:
        base_heart += 25
        base_temp += 2
    if radiation > 7:
        base_temp += 3

    temp = round(base_temp, 2)
    heart = int(base_heart)
    light = round(base_light, 3)
    mode = predict_mode(temp, heart, light)
    if temp >= 40 or heart >= 160 or oxygen <= 60 or radiation >= 8:
        mode = "Alert Mode"

    return temp, heart, light, mode


def get_gradient_by_terrain(terrain):
    terrains = {
        "Forest": ("#184d27", "#0a2e17"),      # deep green tones
        "Rock": ("#5c5c5c", "#2e2e2e"),        # natural rocky greys
        "Desert": ("#cba35b", "#a18445"),      # sandy warm tones
        "Urban": ("#4f4f4f", "#1f1f1f"),       # concrete realism
        "Space": ("#0b0b2b", "#1c1c6b")        # deep navy cosmic
    }
    return terrains.get(terrain, ("#0aa1dd", "#0099cc"))


def blend_mode_and_terrain(mode, terrain):
    terrain_base, terrain_tint = get_gradient_by_terrain(terrain)
    mode_colours = {
        "Cool Mode": ("#4ca1af", "#2c3e50"),        # calm blue-steel
        "Heat Mode": ("#ff914d", "#ff5e00"),        # realistic heat orange
        "Stealth Mode": ("#1e3c1f", "#2a5725"),     # dark camo green
        "Alert Mode": ("#2b0000", "#ff0000"),       # darker, scarier red
    }
    mode_base, mode_tint = mode_colours.get(mode, ("#4ca1af", "#2c3e50"))

    def blend_hex(a, b):
        a, b = int(a.lstrip("#"), 16), int(b.lstrip("#"), 16)
        avg = (a + b) // 2
        return f"#{avg:06x}"

    return blend_hex(terrain_base, mode_base), blend_hex(terrain_tint, mode_tint)


def render_visual(mode, terrain):
    base, tint = blend_mode_and_terrain(mode, terrain)

    if mode == "Alert Mode":
        # More aggressive and darker pulse animation for danger effect
        pulse_speed = "0.8s"
        glow = f"""
        @keyframes danger {{
            0% {{ box-shadow: 0 0 25px {tint}, 0 0 60px {tint}; background: radial-gradient(circle, {base}, #000000); }}
            50% {{ box-shadow: 0 0 120px #ff0000, 0 0 200px #8b0000; background: radial-gradient(circle, #440000, #000000); }}
            100% {{ box-shadow: 0 0 25px {tint}, 0 0 60px {tint}; background: radial-gradient(circle, {base}, #000000); }}
        }}
        """
        animation_name = "danger"
    else:
        pulse_speed = "3s"
        glow = f"""
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 20px {base}, 0 0 40px {tint}; }}
            50% {{ box-shadow: 0 0 80px {base}, 0 0 120px {tint}; }}
            100% {{ box-shadow: 0 0 20px {base}, 0 0 40px {tint}; }}
        }}
        """
        animation_name = "pulse"

    html = f"""
    <style>{glow}</style>
    <div style="
        width:100%;
        height:420px;
        border-radius:20px;
        background:linear-gradient(135deg,{base},{tint});
        animation:{animation_name} {pulse_speed} infinite;
        display:flex;
        align-items:center;
        justify-content:center;
        flex-direction:column;
        color:white;
        font-size:28px;
        font-weight:bold;
        text-shadow:2px 2px 8px rgba(0,0,0,0.9);
    ">
        {mode}<br>
        <span style='font-size:18px; opacity:0.85;'>({terrain} Terrain)</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def export_csv(df):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "session_data.csv", "text/csv")


def generate_qr(link):
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    st.image(buf.getvalue(), caption="Scan to open repo", use_container_width=False)


def generate_metrics():
    return {
        "Core Temp (°C)": round(random.uniform(35, 41), 2),
        "Heart Rate (BPM)": random.randint(60, 160),
        "SpO₂ (%)": random.randint(85, 100),
        "Respiration Rate (/min)": random.randint(12, 30),
        "Sweat Rate (ml/h)": random.randint(300, 800),
        "Suit Pressure (kPa)": round(random.uniform(95, 105), 1),
        "Battery Health (%)": random.randint(60, 100),
        "Radiation Dose (mSv)": round(random.uniform(0.1, 9.5), 2),
        "Oxygen Level (%)": random.randint(50, 100)
    }

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.title("Simulation & System Controls")
scenario = st.sidebar.selectbox("Scenario Preset", ["Normal", "High Exertion", "Low Light", "Overheat"])
terrain = st.sidebar.selectbox("Terrain", ["Forest", "Rock", "Desert", "Urban", "Space"])
oxygen = st.sidebar.slider("Oxygen (%)", 40, 100, 95)
radiation = st.sidebar.slider("Radiation Level (0–10)", 0, 10, 2)
space_mode = st.sidebar.checkbox("Space Mode")
interval = st.sidebar.slider("Refresh Interval (s)", 1, 10, 3)

st.sidebar.markdown("---")
st.sidebar.subheader("Data Options")
if st.sidebar.button("Export CSV"):
    export_csv(st.session_state.history)

st.sidebar.markdown("---")
st.sidebar.subheader("GitHub Repo")
repo_link = st.sidebar.text_input("Enter your repo URL", "https://github.com/thesardonicone/Smart-Adaptive-Camouflage-Suit-Live-Simulation/")
if st.sidebar.button("Show QR"):
    generate_qr(repo_link)

# --------------------------------------------------
# MAIN UI
# --------------------------------------------------
st.markdown("<h1 class='main-title'>Smart Adaptive Camouflage Suit — Live Dashboard</h1>", unsafe_allow_html=True)
placeholder = st.empty()

while True:
    temp, heart, light, mode = simulate_reading(scenario, terrain, oxygen, radiation, space_mode)
    metrics = generate_metrics()

    entry = {"timestamp": datetime.now(UTC).isoformat(), "temp": temp, "heart": heart, "light": light, "mode": mode}
    new_row = pd.DataFrame([entry])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True).tail(300)

    with placeholder.container():
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.subheader("Adaptive Suit Visual")
            st.caption(f"Mode: {mode} — Temp: {temp}°C | Heart: {heart} BPM | Light: {light}")
            render_visual(mode, terrain)

        with col2:
            st.subheader("Physiological Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric("🧠 Core Temp", f"{metrics['Core Temp (°C)']} °C")
            m2.metric("💓 Heart Rate", f"{metrics['Heart Rate (BPM)']} BPM")
            m3.metric("🩸 SpO₂", f"{metrics['SpO₂ (%)']} %")

            m4, m5, m6 = st.columns(3)
            m4.metric("🌬️ Respiration", f"{metrics['Respiration Rate (/min)']} /min")
            m5.metric("💧 Sweat Rate", f"{metrics['Sweat Rate (ml/h)']} ml/h")
            m6.metric("🪖 Suit Pressure", f"{metrics['Suit Pressure (kPa)']} kPa")

            m7, m8, m9 = st.columns(3)
            m7.metric("🔋 Battery Health", f"{metrics['Battery Health (%)']} %")
            m8.metric("☢️ Radiation", f"{metrics['Radiation Dose (mSv)']} mSv")
            m9.metric("🌫️ Oxygen Level", f"{metrics['Oxygen Level (%)']} %")

            st.subheader("Vitals Trend")
            df = st.session_state.history.copy()
            if not df.empty:
                df["temp"] = pd.to_numeric(df["temp"], errors="coerce")
                df["heart"] = pd.to_numeric(df["heart"], errors="coerce")
                fig = px.line(df, x="timestamp", y=["temp", "heart"], title="Temperature & Heart Rate Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data yet.")
    time.sleep(interval)

