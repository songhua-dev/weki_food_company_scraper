import os
import datetime

# 統一設定路徑，確保不論在哪個模組呼叫，log 都會寫入專案目錄
BASE_DIR = r'C:\Python\python_project\P2_food_scraper'
LOG_PATH = os.path.join(BASE_DIR, "process.log")

def log_message(message):
    """記錄訊息到 console 並寫入 process.log"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def print_data_summary(df, stage_name):
    """印出資料摘要並同步寫入 log"""
    summary_header = f"\n--- Data Summary: {stage_name} ---"
    print(summary_header)
    
    # 這裡呼叫 log_message 來同步寫入
    log_message(f"--- Data Summary: {stage_name} ---")
    log_message(f"Total Rows: {len(df)}")
    
    if 'status' in df.columns:
        counts = df['status'].value_counts().to_string()
        print(counts)
        log_message(f"Status Counts:\n{counts}")
    
    print("-" * 30 + "\n")