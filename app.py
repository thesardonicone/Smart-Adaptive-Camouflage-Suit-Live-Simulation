"""
Smart Adaptive Camouflage Suit — ML Integrated Version
Fully compatible with suit_mode_training.py (6-feature model)
"""

import streamlit as st
import random
import json
import joblib
import os
import datetime
from dataclasses import dataclass, asdict

# -------------------------------------------------------
# Utility
# -------------------------------------------------------
def now_str():
    return datetime.datetime.utcnow().isoformat() + "Z"

# -------------------------------------------------------
# Sensor Simulation
# -------------------------------------------------------
@dataclass
class SensorReading:
    rgb: tuple
    lux: float
    cct: float
    temperature_c: float
    imu_yaw: float
    tof_mm: float
    thermal_c: float

def simulate_sensor(env="grass") -> SensorReading:
    presets = {
        "grass": {"rgb":(45,120,35),"lux":12000,"cct":5200,"temp":30,"thermal":28,"tof":200},
        "sand":  {"rgb":(194,178,128),"lux":20000,"cct":6000,"temp":35,"thermal":33,"tof":250},
        "urban": {"rgb":(120,120,120),"lux":15000,"cct":5600,"temp":29,"thermal":29,"tof":180},
        "night": {"rgb":(10,10,20),"lux":50,"cct":3000,"temp":22,"thermal":22,"tof":120},
    }
    base = presets.get(env, presets["grass"])
    j = lambda v,p=0.07: v*(1+random.uniform(-p,p))
    r = int(j(base["rgb"][0]))
    g = int(j(base["rgb"][1]))
    b = int(j(base["rgb"][2]))

    return SensorReading(
        rgb=(r,g,b),
        lux=round(j(base["lux"],0.15),2),
        cct=round(j(base["cct"],0.05),1),
        temperature_c=round(j(base["temp"],0.08),1),
        imu_yaw=round(random.uniform(0,360),1),
        tof_mm=round(j(base["tof"],0.15),1),
        thermal_c=round(j(base["thermal"],0.1),1)
    )

# -------------------------------------------------------
# Actuator Classes
# -------------------------------------------------------
class LEDMatrixActuator:
    def __init__(self,w=16,h=8):
        self.w=w; self.h=h
        self.state=[[(0,0,0)]*w for _ in range(h)]
    def apply_pattern(self,p):
        self.state=p

class EInkActuator:
    def __init__(self,w=8,h=8):
        self.w=w; self.h=h
        self.state=[["white"]*w for _ in range(h)]
    def apply_pattern(self,p):
        self.state=p

class ThermochromicActuator:
    def __init__(self):
        self.map=None
    def apply_pattern(self,p):
        self.map=p

# -------------------------------------------------------
# Power + Safety
# -------------------------------------------------------
class PowerManager:
    def __init__(self,mah=3000,voltage=5):
        self.mah=mah; self.voltage=voltage
    def runtime(self,a=5,c=1,s=0.5):
        wh=(self.mah/1000)*self.voltage
        return round(wh/(a+c+s),2)

class SafetyManager:
    def __init__(self,cutoff=65):
        self.cutoff=cutoff
    def check(self,s:SensorReading):
        issues=[]
        if s.temperature_c>self.cutoff: issues.append("ambient_overheat")
        if s.thermal_c>self.cutoff: issues.append("thermal_overheat")
        if s.tof_mm<50: issues.append("close_surface")
        return issues

# -------------------------------------------------------
# Logger
# -------------------------------------------------------
class DataLogger:
    def __init__(self,folder):
        self.folder=folder
        os.makedirs(folder,exist_ok=True)
    def save(self,sensor,pred,tag):
        name=f"{self.folder}/log_{now_str().replace(':','_')}.json"
        with open(name,"w") as f:
            json.dump({
                "timestamp":now_str(),
                "sensor":asdict(sensor),
                "model":pred,
                "tag":tag
            },f,indent=2)
        return name

# -------------------------------------------------------
# Visibility Metric
# -------------------------------------------------------
def visibility_score(sensor,pattern):
    base=max(0,1-(sensor.lux/50000))
    if pattern.get("type")=="colour_fill":
        r,g,b=pattern["rgb"]
        ambient=sum(sensor.rgb)/3
        pat=(r+g+b)/3
        diff=abs(ambient-pat)/255
    else:
        diff=0.25
    return round(min(1,max(0,base+0.5*diff)),3)

# -------------------------------------------------------
# Load ML Model
# -------------------------------------------------------
MODEL_PATH = os.path.join("models","suit_mode_rf.joblib")

if not os.path.exists(MODEL_PATH):
    st.error("Model not found. Ensure models/suit_mode_rf.joblib exists.")
    st.stop()

rf_model = joblib.load(MODEL_PATH)

# -------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------
st.set_page_config(page_title="Smart Adaptive Camouflage Suit — ML Enhanced",layout="wide")
st.title("Smart Adaptive Camouflage Suit — ML Enhanced")

col1,col2=st.columns([2,1])

with col1:
    env = st.selectbox("Environment",["grass","sand","urban","night"])
    override = st.checkbox("Manual override pattern")
    if override:
        manual = st.color_picker("Pick colour")
    run = st.button("Run Suit Simulation")

with col2:
    st.write("Logs:",len(os.listdir("suit_logs")))

# Instances
led=LEDMatrixActuator()
eink=EInkActuator()
thermo=ThermochromicActuator()
power=PowerManager()
safety=SafetyManager()
logger=DataLogger("suit_logs")

# -------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------
if run:
    sensor = simulate_sensor(env)
    st.write("Sensor Reading:",asdict(sensor))

    issues = safety.check(sensor)
    if issues:
        st.warning("Safety Issues: " + ", ".join(issues))

    # ML INPUT VECTOR (6 FEATURES)
    rgb_avg = sum(sensor.rgb)/3
    feats = [[
        rgb_avg,
        sensor.lux,
        sensor.cct,
        sensor.temperature_c,
        sensor.thermal_c,
        sensor.tof_mm
    ]]

    ml_mode = rf_model.predict(feats)[0]

    # Pattern Mapping
    if ml_mode == "low_light":
        pred = {
            "mode":"low_light",
            "pattern":{"type":"darker"}
        }
    elif ml_mode == "thermal":
        pred = {
            "mode":"thermal",
            "pattern":{"type":"thermal-match"}
        }
    else:
        pred = {
            "mode":"visual_blend",
            "pattern":{"type":"colour_fill","rgb":sensor.rgb}
        }

    if override:
        hx = manual.lstrip("#")
        r,g,b = tuple(int(hx[i:i+2],16) for i in (0,2,4))
        pred["pattern"]={"type":"colour_fill","rgb":(r,g,b)}

    st.write("Model Output:",pred)

    # Actuator Selection
    choice = st.radio("Actuator",["LED","E-Ink","Thermochromic"])

    if choice=="LED":
        pattern = [[pred["pattern"].get("rgb",(0,0,0))]*led.w for _ in range(led.h)]
        led.apply_pattern(pattern)
        st.write("LED Applied")
    elif choice=="E-Ink":
        fill = "dark" if pred["pattern"]["type"]=="darker" else "light"
        p = [[fill]*eink.w for _ in range(eink.h)]
        eink.apply_pattern(p)
        st.write("E-Ink Applied")
    else:
        thermo.apply_pattern({"active":True})
        st.write("Thermochromic Applied")

    st.metric("Visibility Score",visibility_score(sensor,pred["pattern"]))
    st.metric("Estimated Runtime (hrs)",power.runtime())

    log = logger.save(sensor,pred,env)
    st.success(f"Saved: {log}")
