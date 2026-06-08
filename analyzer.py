from datetime import datetime, timedelta


def calculate_hours_since(last_time):
    """
    마지막 카페인 섭취 시간으로부터 현재까지 몇 시간이 지났는지 계산
    """
    now = datetime.now()
    last_datetime = datetime.combine(now.date(), last_time)

    # 입력한 시간이 현재보다 미래라면 전날 섭취로 간주
    if last_datetime > now:
        last_datetime -= timedelta(days=1)

    diff = now - last_datetime
    return round(diff.total_seconds() / 3600, 1)


def analyze_study_condition(caffeine_cups, last_time, focus_score, sleep_hours, fatigue_level, study_goal):
    """
    입력값을 바탕으로 학습 상태를 분석하고
    상태, 위험도 점수, 판단 근거를 반환
    """

    hours_since = calculate_hours_since(last_time)

    risk_score = 0
    reasons = []
    factor_scores = {
        "카페인": 0,
        "섭취 시간": 0,
        "집중도": 0,
        "수면": 0,
        "피로도": 0
    }

    # 1. 카페인 섭취량 분석
    if caffeine_cups >= 4:
        risk_score += 25
        factor_scores["카페인"] = 25
        reasons.append(f"카페인 섭취량이 {caffeine_cups}잔으로 높은 편입니다.")
    elif caffeine_cups >= 2:
        risk_score += 12
        factor_scores["카페인"] = 12
        reasons.append(f"카페인 섭취량이 {caffeine_cups}잔으로 보통 수준입니다.")
    else:
        reasons.append(f"카페인 섭취량이 {caffeine_cups}잔으로 비교적 적절합니다.")

    # 2. 마지막 섭취 시간 분석
    if hours_since < 3:
        risk_score += 20
        factor_scores["섭취 시간"] = 20
        reasons.append(f"마지막 카페인 섭취 후 {hours_since}시간밖에 지나지 않았습니다.")
    elif hours_since < 6:
        risk_score += 10
        factor_scores["섭취 시간"] = 10
        reasons.append(f"마지막 카페인 섭취 후 {hours_since}시간이 지났습니다.")
    else:
        reasons.append(f"마지막 카페인 섭취 후 {hours_since}시간이 지나 영향이 줄어들었을 가능성이 있습니다.")

    # 3. 집중도 분석
    if focus_score < 40:
        risk_score += 25
        factor_scores["집중도"] = 25
        reasons.append(f"집중도가 {focus_score}점으로 매우 낮습니다.")
    elif focus_score < 70:
        risk_score += 12
        factor_scores["집중도"] = 12
        reasons.append(f"집중도가 {focus_score}점으로 다소 낮거나 보통 수준입니다.")
    else:
        reasons.append(f"집중도가 {focus_score}점으로 양호합니다.")

    # 4. 수면 시간 분석
    if sleep_hours < 5:
        risk_score += 25
        factor_scores["수면"] = 25
        reasons.append(f"수면 시간이 {sleep_hours}시간으로 부족합니다.")
    elif sleep_hours < 7:
        risk_score += 12
        factor_scores["수면"] = 12
        reasons.append(f"수면 시간이 {sleep_hours}시간으로 약간 부족합니다.")
    else:
        reasons.append(f"수면 시간이 {sleep_hours}시간으로 비교적 충분합니다.")

    # 5. 피로도 분석
    if fatigue_level == "높음":
        risk_score += 15
        factor_scores["피로도"] = 15
        reasons.append("현재 피로도가 높아 학습 효율이 떨어질 가능성이 있습니다.")
    elif fatigue_level == "보통":
        risk_score += 7
        factor_scores["피로도"] = 7
        reasons.append("현재 피로도는 보통 수준입니다.")
    else:
        reasons.append("현재 피로도가 낮아 학습을 진행하기 좋은 상태입니다.")

    # 위험도 점수는 최대 100으로 제한
    risk_score = min(risk_score, 100)

    # 최종 상태 분류
    if risk_score >= 70:
        status = "위험형"
        summary = "카페인, 수면, 집중도 중 여러 요소에서 학습 효율 저하 가능성이 큽니다."
    elif risk_score >= 40:
        status = "주의형"
        summary = "학습은 가능하지만 카페인 섭취와 컨디션 관리가 필요합니다."
    else:
        status = "건강형"
        summary = "현재 학습 컨디션이 비교적 안정적입니다."

    return {
        "status": status,
        "summary": summary,
        "risk_score": risk_score,
        "hours_since": hours_since,
        "reasons": reasons,
        "factor_scores": factor_scores,
        "study_goal": study_goal
    }