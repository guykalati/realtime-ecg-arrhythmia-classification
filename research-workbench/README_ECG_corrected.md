# ECG heartbeat classification (course team project)

This is a surviving portfolio copy of a three-person course project by Rotem Even Zur, Nevo Levi, and Guy Kalati. The original team repository is [RotemEZ/ECG-Arrhythmia-Classification](https://github.com/RotemEZ/ECG-Arrhythmia-Classification). Guy intends to build a substantially stronger personal version. The original team baseline and new personal work should remain clearly distinguishable.

## What the local files support

`ECG_MITBIH.ipynb` reads `mitbih_train.csv` and `mitbih_test.csv`, each with 187 waveform columns and one class label. Its saved outputs show 87,554 training beats and 21,892 test beats. A five-class 1D CNN's saved test classification report gives accuracy **0.9802**, macro F1 **0.8967**, and weighted F1 **0.9796**. The minority fusion class has recall **0.6852** in that report. These are saved notebook outputs; a clean rerun has not been established.

The CSVs used by the notebook do not expose patient IDs. The notebook cannot establish whether the existing split separates patients. Its validation split is by heartbeat row. The 0.9802 result must not be presented as patient-wise generalization or clinical performance. The repository also contains other models and saved reports with different metrics; each figure must be tied to its exact model and evaluation path.

`ECG_APP.py` only loads `ecg_scaler.pkl` and writes scaler parameters to JSON. It is **not** a Streamlit app or real-time monitoring system. The required scaler file and a working monitoring app are absent from this copy. This copy also lacks the CSV inputs and a documented clean-environment run.

## Files

- `ECG_MITBIH.ipynb`: exploratory modeling notebook with saved outputs and hard-coded Colab paths.
- `ECG_APP.py`: scaler-conversion utility; requires the missing `ecg_scaler.pkl`.
- `ECG_Arrhythmia_Classification_with_Real-time_Hospital_Monitoring_Final.pdf`: original course presentation; its claims require independent checks against code and run artifacts.

The [MIT-BIH Arrhythmia Database](https://physionet.org/content/mitdb/1.0.0/) contains 48 recordings from 47 subjects. A stronger evaluation should rebuild examples from record-linked data so subjects or records can be kept separate across splits. This is a research demonstration only; no clinical deployment or latency claim is established here.
