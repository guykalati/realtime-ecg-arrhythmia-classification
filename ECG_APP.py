import numpy as np
import pickle
import json

# Load your scaler
with open('ecg_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Save scaler parameters as JSON for JavaScript
scaler_params = {
    'mean': scaler.mean_.tolist(),
    'scale': scaler.scale_.tolist()
}

with open('scaler_params.json', 'w') as f:
    json.dump(scaler_params, f)

print("✅ Model conversion complete!")