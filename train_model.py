import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

# Create folders if missing
os.makedirs("models", exist_ok=True)
os.makedirs("data", exist_ok=True)

np.random.seed(42)
rows = []

# Generate synthetic dataset matching the sensor structure in app.py
for _ in range(5000):

    # Sensor fields: aligned EXACTLY with Streamlit simulation
    r = np.random.randint(0, 255)
    g = np.random.randint(0, 255)
    b = np.random.randint(0, 255)
    rgb_avg = (r + g + b) / 3

    lux = np.random.uniform(20, 28000)
    cct = np.random.uniform(3000, 6500)

    ambient_temp = np.random.normal(30, 6)
    thermal_temp = ambient_temp + np.random.normal(0, 3)

    tof = np.random.uniform(50, 400)

    # ML mode rules exactly aligned with app logic
    if lux < 120:
        mode = "low_light"
    elif thermal_temp > 32:
        mode = "thermal"
    else:
        mode = "visual_blend"

    rows.append([rgb_avg, lux, cct, ambient_temp, thermal_temp, tof, mode])

# Build DataFrame
df = pd.DataFrame(rows, columns=[
    "rgb_avg", "lux", "cct",
    "ambient_temp", "thermal_temp", "tof",
    "mode"
])

# Split
X = df[["rgb_avg", "lux", "cct", "ambient_temp", "thermal_temp", "tof"]]
y = df["mode"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(
    n_estimators=180,
    max_depth=None,
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate performance
y_pred = model.predict(X_test)
print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# Save output files
joblib.dump(model, "models/suit_mode_rf.joblib")
df.to_csv("data/synthetic_suit_dataset.csv", index=False)

print("\nSaved model → models/suit_mode_rf.joblib")
print("Saved dataset → data/synthetic_suit_dataset.csv\n")
