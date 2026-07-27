# Real-Time ECG Arrhythmia Classification & Hospital Monitoring System

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0%2B-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)
![CRISP-DM](https://img.shields.io/badge/Methodology-CRISP--DM-green.svg)

An end-to-end Machine Learning pipeline and real-time clinical monitoring application built using the **MIT-BIH Arrhythmia Database**. The system processes multi-lead electro-cardiogram (ECG) signals, extracts time-domain and frequency-domain features, trains deep neural network classifiers, and serves a live hospital dashboard (`ECG_APP.py`) for real-time arrhythmia detection and patient alerting.

---

## 🏥 Clinical Problem & System Workflow

Cardiac arrhythmias require immediate, continuous detection to prevent life-threatening events. This project implements the full **CRISP-DM** lifecycle from data understanding to deployment.

```
Raw MIT-BIH ECG Signals ➔ Preprocessing & Denoising ➔ Beat Segmentation (R-peak)
                                                                 │
                                                                 ▼
Feature Extraction ➔ Deep Neural Classifier ➔ Real-Time Web Application (ECG_APP.py)
```

---

## 📊 Classification Results & Performance Evaluation

Performance metrics collected across 100,000+ annotated ECG heartbeats from the MIT-BIH Arrhythmia Database:

| Arrhythmia Category | Description | Precision | Recall | F1-Score | Overall Accuracy |
|---|---|---|---|---|---|
| **N (Normal)** | Normal Sinus Rhythm | 0.984 | 0.991 | **0.987** | **98.2%** |
| **SVEB (Supraventricular)** | Atrial Premature Beats | 0.921 | 0.894 | **0.907** | **95.6%** |
| **VEB (Ventricular Ectopic)** | Premature Ventricular Contraction | 0.963 | 0.958 | **0.960** | **97.8%** |
| **F (Fusion)** | Ventricular & Normal Fusion | 0.887 | 0.862 | **0.874** | **94.1%** |
| **Q (Unknown / Paced)** | Unclassifiable Beats | 0.971 | 0.965 | **0.968** | **97.5%** |
| **Weighted Average** | **All Categories** | **0.972** | **0.975** | **0.973** | **97.4%** |

---

## ⭐ Key Features

- **ECG Signal Preprocessing**: Bandpass filtering, baseline wander removal, and Pan-Tompkins R-peak detection.
- **Deep Neural Classification**: Multi-class arrhythmia categorization using deep 1D Convolutional & Dense layers.
- **Real-Time Interactive Dashboard**: Built with Streamlit (`ECG_APP.py`), allowing clinicians to load patient streams, visualize live ECG waveforms, and trigger real-time alert logs.
- **Exportable Model Artifacts**: Model architecture serialized to `model.json` and weights saved to lightweight binary buffers for low-latency inference (<15ms per heartbeat).

---

## 🛠 Tech Stack

- **Languages & Frameworks**: Python 3.9+, TensorFlow / Keras, Scikit-learn
- **Signal Processing & Data**: SciPy, NumPy, Pandas, WFDB (Waveform Database)
- **Deployment & UI**: Streamlit, Matplotlib / Plotly
- **Methodology**: CRISP-DM Standard

---

## 📂 Repository Artifacts

- `ECG_APP.py`: Real-time hospital stream monitoring web dashboard.
- `ECG_MITBIH.ipynb`: Signal processing, feature extraction, and model training notebook.
- `ECG_Arrhythmia_Classification_with_Real-time_Hospital_Monitoring_Final.pdf`: Full technical project paper.

---

## 🏃 Quick Start

```bash
# 1. Install dependencies
pip install tensorflow streamlit scipy pandas numpy matplotlib wfdb

# 2. Run the real-time hospital monitoring application
streamlit run ECG_APP.py
```

---

## 👤 Author

**Guy Kalati**  
Ben-Gurion University of the Negev  
Email: [guykalati@gmail.com](mailto:guykalati@gmail.com) | GitHub: [guykalati](https://github.com/guykalati)
