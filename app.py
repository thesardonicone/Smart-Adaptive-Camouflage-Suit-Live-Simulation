# ----------------------------
# STEP-BY-STEP PLAN (compact)
# ----------------------------
# 1) Requirements: define measurable objectives (target environments, response time, max power, weight).
# 2) Sensing & data collection: ambient RGB, lux, CCT, IMU, TOF/texture proxy, thermal IR.
# 3) Control pipeline: tiny ML or rule-based mapping sensor vector -> pixel/pattern commands.
# 4) Actuation: modular patches: flexible LED matrix, addressable e-ink, thermochromic film demo.
# 5) Power & thermal design: battery sizing, power gating, thermal cutoffs.
# 6) Software: event-driven Streamlit UI, sensor simulator, logging, unit tests.
# 7) Safety & UX: failure modes, manual override, diagnostics.
# 8) Build/test: rapid prototyping and iterative data collection.
# 9) Deliverables: demo/video, poster, BOM, block diagrams, power budget, test results, repo.

# ----------------------------
# Minimal runnable skeleton
# ----------------------------
import streamlit as st
import time
import math
import json
import random
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Optional
import datetime
import os

# ---------- Configuration ----------
APP_TITLE = "Smart Adaptive Camouflage Suit — Demo"
DATA_DIR = "/mnt/data/suit_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- Utilities ----------
def now_str():
    return datetime.datetime.utcnow().isoformat() + "Z"

# ---------- Sensor simulator ----------
@dataclass
class SensorReading:
    rgb: Tuple[int,int,int]            # ambient RGB
    lux: float                         # illuminance
    cct: float                         # correlated colour temperature (K)
    temperature_c: float               # ambient temperature
    imu_yaw: float                     # orientation proxy
    tof_mm: float                      # short-range distance as texture proxy
    thermal_c: float                   # thermal reading (IR)

def simulate_sensor(environment: str = "grass") -> SensorReading:
    # Basic presets for demo environments
    presets = {
        "grass": {"rgb":(45,120,35),"lux":12000,"cct":5200,"temperature_c":30,"thermal_c":28,"tof_mm":200},
        "sand":  {"rgb":(194,178,128),"lux":20000,"cct":6000,"temperature_c":35,"thermal_c":33,"tof_mm":250},
        "urban": {"rgb":(120,120,120),"lux":15000,"cct":5600,"temperature_c":29,"thermal_c":29,"tof_mm":180},
        "night": {"rgb":(10,10,20),"lux":50,"cct":3000,"temperature_c":22,"thermal_c":22,"tof_mm":120},
    }
    base = presets.get(environment, presets["grass"])
    jitter = lambda v, pct=0.05: int(v*(1 + random.uniform(-pct,pct))) if isinstance(v,int) else v*(1 + random.uniform(-pct,pct))
    return SensorReading(
        rgb=(jitter(base["rgb"][0]), jitter(base["rgb"][1]), jitter(base["rgb"][2])),
        lux=jitter(base["lux"], 0.12),
        cct=jitter(base["cct"], 0.05),
        temperature_c=round(jitter(base["temperature_c"], 0.06),1),
        imu_yaw=round(random.uniform(0,360),1),
        tof_mm=round(jitter(base["tof_mm"], 0.15),1),
        thermal_c=round(jitter(base["thermal_c"], 0.08),1),
    )

# ---------- Actuator interface stubs ----------
class ActuatorInterface:
    def apply_pattern(self, pattern: Any) -> None:
        """Apply a visual pattern to the actuator patch (override)."""
        raise NotImplementedError

class LEDMatrixActuator(ActuatorInterface):
    def __init__(self, width=16, height=8):
        self.width = width
        self.height = height
        self.state = [[(0,0,0) for _ in range(width)] for _ in range(height)]
    def apply_pattern(self, pattern):
        # pattern: list of rows with (r,g,b) tuples or single RGB value
        self.state = pattern
        # In hardware, here we'd convert state to SPI/I2C updates.
    def preview_summary(self):
        return {"type":"LEDMatrix","size":(self.width,self.height)}

class EInkActuator(ActuatorInterface):
    def __init__(self, cols=8, rows=8):
        self.cols = cols
        self.rows = rows
        self.state = [["white" for _ in range(cols)] for _ in range(rows)]
    def apply_pattern(self, pattern):
        self.state = pattern
    def preview_summary(self):
        return {"type":"EInk","size":(self.cols,self.rows)}

class ThermochromicDemo(ActuatorInterface):
    def __init__(self):
        self.heat_map = None
    def apply_pattern(self, pattern):
        # pattern could be a greyscale intensity map representing heat to apply
        self.heat_map = pattern
    def preview_summary(self):
        return {"type":"Thermochromic","note":"Passive demo (requires heat sources in real hardware)"}

# ---------- TinyML / Decision model stubs ----------
class TinyDecisionModel:
    def __init__(self):
        # Simple rule thresholds can be replaced by a TinyML model later.
        self.rules = {
            "dark_threshold": 100,  # lux
            "thermal_threshold": 25
        }
    def predict(self, sensor: SensorReading) -> Dict[str,Any]:
        # Return a simple mode and a pattern descriptor
        if sensor.lux < self.rules["dark_threshold"]:
            mode = "low_light"
            pattern = {"type":"darker","info":"reduce brightness, increase contrast edges"}
        elif sensor.thermal_c > self.rules["thermal_threshold"] + 5:
            mode = "thermal"
            pattern = {"type":"thermal-match","info":"use thermochromic prototypes"}
        else:
            mode = "visual_blend"
            # Simple colour match: pick ambient RGB as dominant colour
            pattern = {"type":"colour_fill","rgb":sensor.rgb}
        return {"mode":mode,"pattern":pattern}

# ---------- Power & safety managers ----------
class PowerManager:
    def __init__(self, battery_mah=2000, voltage=5.0):
        self.battery_mah = battery_mah
        self.voltage = voltage
    def worst_case_power_w(self, actuator_power_w=5.0, controller_power_w=1.0, sensors_power_w=0.5):
        return actuator_power_w + controller_power_w + sensors_power_w
    def expected_runtime_hours(self, actuator_power_w=5.0, controller_power_w=1.0, sensors_power_w=0.5):
        total_w = self.worst_case_power_w(actuator_power_w, controller_power_w, sensors_power_w)
        # Convert mAh at voltage to Wh: (mAh/1000)*V = Wh
        wh = (self.battery_mah/1000.0) * self.voltage
        if total_w <= 0:
            return float("inf")
        return wh / total_w

class SafetyManager:
    def __init__(self, temp_cutoff_c=60.0):
        self.temp_cutoff_c = temp_cutoff_c
    def check(self, sensor: SensorReading) -> List[str]:
        issues = []
        if sensor.temperature_c > self.temp_cutoff_c:
            issues.append("ambient_over_temp")
        if sensor.thermal_c > self.temp_cutoff_c:
            issues.append("thermal_patch_over_temperature")
        if sensor.tof_mm < 50:
            issues.append("collision_risk_close_surface")
        return issues

# ---------- Data logger and dataset utilities ----------
class DataLogger:
    def __init__(self, dirpath=DATA_DIR):
        self.dirpath = dirpath
    def save_reading(self, sensor: SensorReading, model_output: Dict[str,Any], tag: Optional[str]=None):
        ts = now_str().replace(":","_")
        fname = os.path.join(self.dirpath, f"reading_{ts}.json")
        payload = {"timestamp": now_str(), "sensor": asdict(sensor), "model": model_output, "tag": tag}
        with open(fname, "w") as f:
            json.dump(payload, f, indent=2)
        return fname
    def list_saved(self):
        return sorted([p for p in os.listdir(self.dirpath) if p.endswith(".json")])

# ---------- Demo / evaluation utilities ----------
def evaluate_pattern_visibility(sensor: SensorReading, pattern: Dict[str,Any]) -> float:
    """
    Dummy evaluation that returns a 'visibility score' (lower is better).
    In real tests, you'd compute contrast against background using camera or
    human-subject testing; here we simulate a score for demonstration.
    """
    # Lower lux -> night => visibility decreases with contrast
    base = max(0.0, 1.0 - (sensor.lux / 50000.0))
    # colour distance penalty
    if pattern.get("type") == "colour_fill" and "rgb" in pattern:
        r,g,b = pattern["rgb"]
        ambient = sum(sensor.rgb)/3
        pat_avg = (r+g+b)/3
        colour_penalty = abs(ambient - pat_avg) / 255.0
    else:
        colour_penalty = 0.2
    score = base + 0.5*colour_penalty
    return max(0.0, min(1.0, score))

# ---------- Streamlit UI (event-driven) ----------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

col1, col2 = st.columns([2,1])

with col1:
    env = st.selectbox("Demo environment", ["grass","sand","urban","night"], index=0)
    manual_override = st.checkbox("Enable manual override of pattern", value=False)
    if manual_override:
        manual_rgb = st.color_picker("Manual fill colour", "#2d7823")
    else:
        manual_rgb = None
    run_demo = st.button("Sample sensors & run model")

with col2:
    st.markdown("**Status**")
    st.text(f"Data directory: {DATA_DIR}")
    saved_files = DataLogger(DATA_DIR).list_saved()
    st.text(f"Saved readings: {len(saved_files)}")

# Instantiate modules
model = TinyDecisionModel()
led_act = LEDMatrixActuator(width=16,height=8)
eink_act = EInkActuator(cols=8,rows=8)
thermo_act = ThermochromicDemo()
pm = PowerManager(battery_mah=3000, voltage=5.0)
safety = SafetyManager(temp_cutoff_c=65.0)
logger = DataLogger(DATA_DIR)

if run_demo:
    sensor = simulate_sensor(env)
    st.write("Sensor reading (simulated):", asdict(sensor))
    issues = safety.check(sensor)
    if issues:
        st.warning("Safety issues detected: " + ", ".join(issues))
    # Model prediction
    pred = model.predict(sensor)
    st.write("Model output:", pred)
    # If manual override, create simple pattern
    if manual_override and manual_rgb:
        # convert hex to rgb
        hexcode = manual_rgb.lstrip("#")
        r,g,b = tuple(int(hexcode[i:i+2],16) for i in (0,2,4))
        pred["pattern"] = {"type":"colour_fill","rgb":(r,g,b)}
    # Apply to chosen actuator for demo
    actuator_choice = st.radio("Actuator preview", ["LED matrix","E-Ink","Thermochromic demo"])
    if actuator_choice == "LED matrix":
        pattern = [[pred["pattern"].get("rgb",(0,0,0)) for _ in range(led_act.width)] for _ in range(led_act.height)]
        led_act.apply_pattern(pattern)
        st.write("LED actuator preview:", led_act.preview_summary())
    elif actuator_choice == "E-Ink":
        pattern = [[ "dark" if pred["pattern"].get("type")=="darker" else "light" for _ in range(eink_act.cols)] for _ in range(eink_act.rows)]
        eink_act.apply_pattern(pattern)
        st.write("E-Ink actuator preview:", eink_act.preview_summary())
    else:
        thermo_act.apply_pattern({"demo":True})
        st.write("Thermochromic demo preview:", thermo_act.preview_summary())
    # Evaluate visibility score and power estimate
    score = evaluate_pattern_visibility(sensor, pred["pattern"])
    runtime = pm.expected_runtime_hours(actuator_power_w=5.0, controller_power_w=1.0, sensors_power_w=0.5)
    st.metric("Simulated visibility score (lower better)", f"{score:.3f}")
    st.metric("Estimated runtime hours (worst-case)", f"{runtime:.2f} h")
    # Save reading and model output
    saved = logger.save_reading(sensor, pred, tag=env)
    st.success(f"Saved reading to {saved}")

# ---------- Extra: debug / dev helpers ----------
with st.expander("Developer notes & next steps"):
    st.markdown("""
    **Next steps to make this buildable**
    - Replace the TinyDecisionModel rules with a quantised TinyML model (TensorFlow Lite for Microcontrollers).
    - Swap the simulator inputs for real sensor inputs (I2C or SPI drivers).
    - Implement actuator drivers for your chosen hardware (APA102/WS2812 for LEDs; SPI for e-ink).
    - Add a power gating MOSFET controlled by the controller for actuator sleep modes.
    - Implement unit tests and integrate data collection into a reproducible dataset (CSV/IMG pairs).
    - Document BOM, block diagrams, and a power budget table for the poster.
    """)
    st.markdown("**Short checklist for the competition poster**")
    st.write("- Problem statement\n- Approach (sensing, decision, actuation)\n- Hardware block diagram and BOM\n- Power budget and thermal safety\n- Demo results and visibility score\n- Future work and scalability notes")

# End of file
