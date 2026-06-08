import streamlit as st
from datetime import time

from analyzer import analyze_study_condition
from feedback_generator import generate_feedback
from storage import save_log, load_logs


st.set_page_config(
    page_title="StudyCaffeine Agent",
    page_icon="☕",
    layout="wide"
)

st.title("☕ StudyCaffeine Agent")
st.write("카페인 섭취량, 수면 시간, 집중도, 피로도를 바탕으로 학습 상태를 분석하는 AI Agent입니다.")

st.divider()


# -----------------------------
# 사이드바 설명
# -----------------------------
with st.sidebar:
    st.header("프로젝트 설명")
    st.write(
        """
        이 사이트는 대학생의 학습 컨디션을 분석하기 위한 AI Agent입니다.

        입력값:
        - 카페인 섭취량
        - 마지막 카페인 섭취 시간
        - 집중도
        - 수면 시간
        - 피로도
        - 오늘의 공부 목표

        출력값:
        - 건강형 / 주의형 / 위험형
        - 위험도 점수
        - 판단 근거
        - 맞춤형 피드백
        - 최근 기록 시각화
        """
    )


# -----------------------------
# 입력 영역
# -----------------------------
st.header("📌 학습 상태 입력")

col1, col2 = st.columns(2)

with col1:
    caffeine_cups = st.number_input(
        "카페인 섭취량을 입력하세요",
        min_value=0,
        max_value=10,
        value=2,
        step=1
    )

    last_time = st.time_input(
        "마지막 카페인 섭취 시간을 입력하세요",
        value=time(14, 0)
    )

    focus_score = st.slider(
        "현재 집중도를 입력하세요",
        min_value=0,
        max_value=100,
        value=70,
        step=1
    )

with col2:
    sleep_hours = st.number_input(
        "지난밤 수면 시간을 입력하세요",
        min_value=0.0,
        max_value=12.0,
        value=7.0,
        step=0.5
    )

    fatigue_level = st.selectbox(
        "현재 피로도를 선택하세요",
        ["낮음", "보통", "높음"]
    )

    study_goal = st.text_input(
        "오늘의 공부 목표를 입력하세요",
        placeholder="예: 데이터분석 과제 마무리, 시험 범위 복습"
    )


st.divider()


# -----------------------------
# 분석 실행
# -----------------------------
if st.button("분석하기", type="primary"):
    input_data = {
        "caffeine_cups": caffeine_cups,
        "last_time": last_time.strftime("%H:%M"),
        "focus_score": focus_score,
        "sleep_hours": sleep_hours,
        "fatigue_level": fatigue_level,
        "study_goal": study_goal
    }

    analysis_result = analyze_study_condition(
        caffeine_cups=caffeine_cups,
        last_time=last_time,
        focus_score=focus_score,
        sleep_hours=sleep_hours,
        fatigue_level=fatigue_level,
        study_goal=study_goal
    )

    feedback_result = generate_feedback(
        analysis_result=analysis_result,
        caffeine_cups=caffeine_cups,
        focus_score=focus_score,
        sleep_hours=sleep_hours,
        fatigue_level=fatigue_level,
        study_goal=study_goal
    )

    save_log(input_data, analysis_result)

    st.header("✅ 분석 결과")

    # 결과 카드
    card1, card2, card3 = st.columns(3)

    with card1:
        st.metric("상태", analysis_result["status"])

    with card2:
        st.metric("위험도 점수", f"{analysis_result['risk_score']} / 100")

    with card3:
        st.metric("마지막 섭취 후 경과", f"{analysis_result['hours_since']}시간")

    # 상태별 메시지
    if analysis_result["status"] == "건강형":
        st.success(analysis_result["summary"])
    elif analysis_result["status"] == "주의형":
        st.warning(analysis_result["summary"])
    else:
        st.error(analysis_result["summary"])

    # 위험도 progress bar
    st.subheader("📊 위험도 시각화")
    st.progress(analysis_result["risk_score"] / 100)

    # 항목별 위험 점수
    st.subheader("📌 항목별 위험 요인")
    factor_scores = analysis_result["factor_scores"]

    factor_col1, factor_col2, factor_col3, factor_col4, factor_col5 = st.columns(5)

    with factor_col1:
        st.metric("카페인", factor_scores["카페인"])
    with factor_col2:
        st.metric("섭취 시간", factor_scores["섭취 시간"])
    with factor_col3:
        st.metric("집중도", factor_scores["집중도"])
    with factor_col4:
        st.metric("수면", factor_scores["수면"])
    with factor_col5:
        st.metric("피로도", factor_scores["피로도"])

    # 판단 근거
    st.subheader("🔎 판단 근거")
    for reason in analysis_result["reasons"]:
        st.write(f"- {reason}")

    # 맞춤형 피드백
    st.subheader("💬 맞춤형 피드백")
    for feedback in feedback_result["feedback"]:
        st.write(f"- {feedback}")

    # 학습 전략
    st.subheader("📚 추천 학습 전략")
    for strategy in feedback_result["study_strategy"]:
        st.write(f"- {strategy}")


# -----------------------------
# 기록 시각화
# -----------------------------
st.divider()
st.header("📈 최근 분석 기록")

logs = load_logs()

if logs.empty:
    st.info("아직 저장된 분석 기록이 없습니다. 분석을 실행하면 기록이 저장됩니다.")
else:
    st.subheader("최근 기록표")
    st.dataframe(logs.tail(10), use_container_width=True)

    st.subheader("위험도 점수 변화")
    chart_data = logs[["created_at", "risk_score"]].copy()
    chart_data = chart_data.set_index("created_at")
    st.line_chart(chart_data)

    st.subheader("집중도 / 수면 시간 / 카페인 섭취량 변화")
    trend_data = logs[["created_at", "focus_score", "sleep_hours", "caffeine_cups"]].copy()
    trend_data = trend_data.set_index("created_at")
    st.line_chart(trend_data)