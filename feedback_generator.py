def generate_feedback(analysis_result, caffeine_cups, focus_score, sleep_hours, fatigue_level, study_goal):
    """
    분석 결과를 바탕으로 사용자 맞춤형 피드백 생성
    """

    status = analysis_result["status"]
    feedback = []
    study_strategy = []

    # 상태별 기본 피드백
    if status == "건강형":
        feedback.append("현재 컨디션은 비교적 안정적입니다. 계획한 학습을 그대로 진행해도 좋습니다.")
        study_strategy.append("새로운 개념 학습이나 문제 풀이처럼 집중력이 필요한 작업을 추천합니다.")

    elif status == "주의형":
        feedback.append("학습은 가능하지만 무리하면 집중력이 빠르게 떨어질 수 있습니다.")
        study_strategy.append("25분 공부 후 5분 휴식하는 방식으로 학습 리듬을 유지하는 것을 추천합니다.")

    else:
        feedback.append("현재 상태에서는 장시간 집중 학습보다 회복과 가벼운 학습이 우선입니다.")
        study_strategy.append("새로운 개념 학습보다는 복습, 정리, 체크리스트 작업을 추천합니다.")

    # 카페인 관련 피드백
    if caffeine_cups >= 4:
        feedback.append("오늘은 추가 카페인 섭취를 피하는 것이 좋습니다.")
    elif caffeine_cups >= 2:
        feedback.append("카페인 섭취량이 보통 이상이므로 늦은 시간 추가 섭취는 피하는 것이 좋습니다.")
    else:
        feedback.append("현재 카페인 섭취량은 과도하지 않은 편입니다.")

    # 수면 관련 피드백
    if sleep_hours < 5:
        feedback.append("수면 시간이 부족하므로 카페인보다 휴식이 더 중요합니다.")
        study_strategy.append("가능하다면 15~20분 정도 짧은 휴식을 먼저 취한 뒤 학습을 시작하세요.")
    elif sleep_hours < 7:
        feedback.append("수면이 약간 부족하므로 오늘 밤에는 카페인 섭취를 줄이고 일찍 자는 것이 좋습니다.")

    # 집중도 관련 피드백
    if focus_score < 40:
        feedback.append("현재 집중도가 낮기 때문에 어려운 과제보다 단순 정리 작업부터 시작하는 것이 좋습니다.")
    elif focus_score < 70:
        feedback.append("집중도가 보통 수준이므로 짧은 단위로 목표를 나누는 것이 좋습니다.")
    else:
        feedback.append("집중도가 양호하므로 중요한 학습 목표를 먼저 처리하는 것이 좋습니다.")

    # 피로도 관련 피드백
    if fatigue_level == "높음":
        feedback.append("피로도가 높기 때문에 카페인으로 억지로 버티기보다 휴식 시간을 포함하는 것이 좋습니다.")

    # 공부 목표 기반 피드백
    if study_goal.strip():
        study_strategy.append(f"오늘의 목표인 '{study_goal}'은 작은 단위로 나누어 진행하는 것이 좋습니다.")

    return {
        "feedback": feedback,
        "study_strategy": study_strategy
    }