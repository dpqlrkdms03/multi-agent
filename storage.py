from pathlib import Path
from datetime import datetime
import pandas as pd

DATA_DIR = Path("data")
LOG_FILE = DATA_DIR / "user_logs.csv"


def save_log(input_data, analysis_result):
    """
    사용자 입력값과 분석 결과를 CSV 파일에 저장
    """

    DATA_DIR.mkdir(exist_ok=True)

    row = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "caffeine_cups": input_data["caffeine_cups"],
        "last_time": input_data["last_time"],
        "focus_score": input_data["focus_score"],
        "sleep_hours": input_data["sleep_hours"],
        "fatigue_level": input_data["fatigue_level"],
        "study_goal": input_data["study_goal"],
        "status": analysis_result["status"],
        "risk_score": analysis_result["risk_score"]
    }

    if LOG_FILE.exists():
        df = pd.read_csv(LOG_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")


def load_logs():
    """
    저장된 분석 기록 불러오기
    """

    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE)

    return pd.DataFrame()