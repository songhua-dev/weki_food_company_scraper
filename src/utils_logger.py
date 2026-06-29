import os
import datetime

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOG_PATH = os.path.join(DATA_DIR, "process.log")

os.makedirs(DATA_DIR, exist_ok=True)

def log_message(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def log_loading(csv_path):
    filename = os.path.basename(csv_path)
    log_message(f"Loading data from {filename}")