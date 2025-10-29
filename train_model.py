import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

# Ensure folders exist
os.makedirs('models', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Generate synthetic data
np.random.seed(42)
rows = []
for _ in range(2000):
    temp = np.random.normal(35, 5) if np.random.rand() > 0.2 else np.random.normal(25, 3)
    heart = int(np.random.normal(80, 15))
    light = np.clip(np.random.beta(2, 2), 0, 1)

    if heart > 130 or temp > 42:
        mode = 'Alert Mode'
    elif light < 0.25:
        mode = 'Stealth Mode'
    elif temp > 34:
        mode = 'Cool Mode'
    elif temp < 20:
        mode = 'Heat Mode'
    else:
        mode = 'Cool Mode'

    rows.append((temp, heart, light, mode))

# Create DataFrame
df = pd.DataFrame(rows, columns=['temp', 'heart', 'light', 'mode'])
X = df[['temp', 'heart', 'light']]
y = df['mode']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model training
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print('Confusion matrix:\n', confusion_matrix(y_test, y_pred))

# Save model and data
joblib.dump(model, 'models/suit_mode_rf.joblib')
df.to_csv('data/synthetic_dataset.csv', index=False)
