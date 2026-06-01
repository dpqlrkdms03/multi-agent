"""StudyCaffeine Agent v0

SAMPLE_INPUT를 순서대로 처리하는 아주 단순한 버전이다.
"""

import re
import json
import csv
import os
import urllib.error
import urllib.request
from pathlib import Path

# 중앙 설정
CONFIG = {
    "LATE_HOUR": 18,
    "HIGH_CAFFEINE": 4,
    "MEDIUM_CAFFEINE": 2,
    "LOW_SLEEP": 6,
    "LOW_FOCUS": 75,
}

# LLM 사용 여부 플래그: False이면 규칙 기반 분석 사용
USE_LLM = os.environ.get("USE_LLM", "False").strip().lower() in {"1", "true", "yes", "on"}
# 검토용 LLM 사용 여부 플래그: 기본값은 False
USE_LLM_REVIEW = os.environ.get("USE_LLM_REVIEW", "False").strip().lower() in {"1", "true", "yes", "on"}


def fetch_external_context(query: str) -> dict:
    """보조 도구/외부 자원에서 최근 기록 일부를 읽어온다.

    - `caffeine_report.md`를 우선 확인하고, 없으면 `caffeine_log.csv`를 확인한다.
    - 파일이 없거나 읽기 실패 시 빈 데이터로 반환한다.
    - 성공/실패 여부는 짧게 터미널에 출력한다.
    """
    report_path = Path("caffeine_report.md")
    log_path = Path("caffeine_log.csv")

    if report_path.exists():
        try:
            lines = report_path.read_text(encoding="utf-8").splitlines()
            recent = lines[-12:] if len(lines) > 12 else lines
            print("외부 자원 연결 성공: caffeine_report.md")
            return {
                "source": "caffeine_report.md",
                "query": query,
                "recent_lines": recent,
            }
        except Exception:
            print("외부 자원 연결 실패: caffeine_report.md")

    if log_path.exists():
        try:
            rows = list(csv.DictReader(log_path.open(encoding="utf-8")))
            recent_rows = rows[-5:] if len(rows) > 5 else rows
            print("외부 자원 연결 성공: caffeine_log.csv")
            return {
                "source": "caffeine_log.csv",
                "query": query,
                "recent_rows": recent_rows,
            }
        except Exception:
            print("외부 자원 연결 실패: caffeine_log.csv")

    print("외부 자원 없음: 빈 데이터 사용")
    return {}


SAMPLE_INPUT = """
[기록 1]
- 카페인 섭취량: 2잔
- 마지막 섭취 시간: 14:00
- 집중도: 85
- 수면 시간: 8시간

[기록 2]
- 카페인 섭취량: 4잔
- 마지막 섭취 시간: 18:30
- 집중도: 70
- 수면 시간: 5시간

[기록 3]
- 카페인 섭취량: 1잔
- 마지막 섭취 시간: 10:00
- 집중도: 90
- 수면 시간: 7시간
""".strip()


def _parse_time_to_hhmm(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "확인 필요"

    # HH:MM 형태
    m = re.search(r"(\d{1,2}):(\d{2})", text)
    if m:
        hh = int(m.group(1)) % 24
        mm = int(m.group(2)) % 60
        return f"{hh:02d}:{mm:02d}"

    # 오전/오후 한글 형태
    m = re.search(r"오전\s*(\d{1,2})시(?:\s*(\d{1,2})분)?", text)
    if m:
        hh = int(m.group(1)) % 12
        mm = int(m.group(2) or 0) % 60
        return f"{hh:02d}:{mm:02d}"
    m = re.search(r"오후\s*(\d{1,2})시(?:\s*(\d{1,2})분)?", text)
    if m:
        hh = (int(m.group(1)) % 12) + 12
        mm = int(m.group(2) or 0) % 60
        return f"{hh:02d}:{mm:02d}"

    # AM/PM 영어 표기
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)", text)
    if m:
        hh = int(m.group(1)) % 12
        mm = int(m.group(2)) % 60
        ampm = m.group(3).lower()
        if ampm == "pm":
            hh += 12
        return f"{hh:02d}:{mm:02d}"

    # 숫자와 '시'만 있는 경우
    m = re.search(r"(\d{1,2})시(?:\s*(\d{1,2})분)?", text)
    if m:
        hh = int(m.group(1)) % 24
        mm = int(m.group(2) or 0) % 60
        return f"{hh:02d}:{mm:02d}"

    return "확인 필요"


def _parse_sleep_hours(text: str):
    text = (text or "").strip()
    if not text:
        return "확인 필요"

    # 예: 7.5, 7시간, 6h30m, 6h 30m, 6시간 30분
    m = re.search(r"(\d+(?:[\.,]\d+)?)\s*(시간|h|hr|hours)?", text)
    if m:
        val = float(m.group(1).replace(",", "."))
        return val

    # h and m 형태
    m = re.search(r"(\d{1,2})\s*h(?:[:\s]?(\d{1,2}))?", text)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2) or 0)
        return hh + mm / 60.0

    # 한글 '시간'과 '분' 조합
    m = re.search(r"(\d{1,2})시간(?:\s*(\d{1,2})분)?", text)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2) or 0)
        return hh + mm / 60.0

    # 숫자만 추출
    m = re.search(r"\d+(?:[\.,]\d+)?", text)
    if m:
        return float(m.group(0).replace(",", "."))

    return "확인 필요"


def extract_facts(text: str) -> list[dict]:
    """기록 블록을 읽어서 중간 정보 dict 리스트로 반환한다."""
    records = []
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]

        # 기본값
        caffeine_amount = "확인 필요"
        last_caffeine_time = "확인 필요"
        focus_score = "확인 필요"
        sleep_hours = "확인 필요"

        for line in lines:
            if "카페인 섭취량" in line:
                m = re.search(r"(\d+)", line)
                if m:
                    caffeine_amount = int(m.group(1))
            elif "마지막 섭취 시간" in line:
                last_caffeine_time = _parse_time_to_hhmm(line)
            elif "집중도" in line:
                m = re.search(r"(\d{1,3})", line)
                if m:
                    val = int(m.group(1))
                    if 0 <= val <= 100:
                        focus_score = val
            elif "수면 시간" in line:
                val = _parse_sleep_hours(line)
                if val != "확인 필요":
                    # 정수면 int로, 소수면 float
                    sleep_hours = val if isinstance(val, float) else float(val)

        # 파생 정보
        if isinstance(sleep_hours, (int, float)):
            sleep_status = "충분" if sleep_hours >= 7 else "부족"
        else:
            sleep_status = "확인 필요"

        # 카페인 위험도 간단 휴리스틱
        caffeine_risk = "확인 필요"
        if isinstance(caffeine_amount, int):
            if caffeine_amount >= CONFIG["HIGH_CAFFEINE"]:
                caffeine_risk = "높음"
            elif caffeine_amount >= CONFIG["MEDIUM_CAFFEINE"]:
                caffeine_risk = "보통"
            else:
                caffeine_risk = "낮음"

        # 시간 기반 가중치: 늦게 마셨고 수면이 짧으면 위험도 상향
        if last_caffeine_time != "확인 필요" and isinstance(sleep_hours, (int, float)):
            try:
                last_hour = int(last_caffeine_time.split(":")[0])
                if last_hour >= CONFIG["LATE_HOUR"] and sleep_hours < CONFIG["LOW_SLEEP"]:
                    caffeine_risk = "높음"
            except Exception:
                pass

        records.append(
            {
                "caffeine_amount": caffeine_amount,
                "last_caffeine_time": last_caffeine_time,
                "focus_score": focus_score,
                "sleep_hours": sleep_hours,
                "sleep_status": sleep_status,
                "caffeine_risk": caffeine_risk,
            }
        )

    return records


def analyze_with_groq(text: str, external_context: dict | None = None) -> list[dict]:
    """Groq 기반 분석을 호출하는 자리표시 함수입니다.

    GROQ_API_KEY가 없거나 호출이 실패하면 예외를 올려
    `analyze_input()`에서 규칙 기반 분석으로 되돌아가게 합니다.
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY가 없습니다")

    prompt = {
        "text": text,
        "external_context": external_context or {},
        "instruction": "카페인 섭취량, 마지막 섭취 시간, 집중도, 수면 시간을 중간 정보 dict list로 추출하세요.",
    }
    payload = json.dumps(
        {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": "You extract structured caffeine study data."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "temperature": 0,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        raise ValueError("Groq 응답 형식이 예상과 다릅니다")
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Groq 호출 실패: {exc}") from exc


def analyze_with_rules(text: str, external_context: dict | None = None) -> list[dict]:
    """규칙 기반 분석: 현재는 extract_facts()를 그대로 사용합니다.

    외부 보조 정보가 있으면 향후 참조할 수 있도록 인자로만 받습니다.
    """
    return extract_facts(text)


def analyze_input(text: str, external_context: dict | None = None) -> list[dict]:
    """입력 텍스트를 분석하여 중간 정보 리스트를 반환합니다.

    - `USE_LLM`이 True이면 `analyze_with_groq` 호출(현재 미구현)
    - False면 규칙 기반(`analyze_with_rules`)을 사용
    """
    if external_context is None:
        external_context = fetch_external_context(text)

    if USE_LLM:
        try:
            print("LLM 분석 시도: Groq")
            return analyze_with_groq(text, external_context=external_context)
        except Exception:
            print("LLM 실패, 규칙 기반 분석으로 전환")
            return analyze_with_rules(text, external_context=external_context)

    return analyze_with_rules(text, external_context=external_context)


def classify_items(records: list[dict]) -> list[dict]:
    """새로 추출된 중간 정보를 이용해 상태를 분류한다."""
    classified = []

    for record in records:
        caffeine = record.get("caffeine_amount")
        last_time = record.get("last_caffeine_time")
        focus = record.get("focus_score")
        sleep = record.get("sleep_hours")
        risk = record.get("caffeine_risk")

        status = "건강형"
        reasons: list[str] = []

        # 불충분 입력 검사
        missing = []
        for k in ("caffeine_amount", "last_caffeine_time", "focus_score", "sleep_hours"):
            if record.get(k) == "확인 필요":
                missing.append(k)
        if missing:
            reasons.append("불충분 입력: " + ",".join(missing))

        # 마지막 섭취 시간 기반 플래그
        late_flag = False
        if last_time != "확인 필요":
            try:
                last_hour = int(last_time.split(":")[0])
                late_flag = last_hour >= CONFIG["LATE_HOUR"]
                if late_flag:
                    reasons.append(f"늦은 섭취({last_time})")
            except Exception:
                pass

        # 위험형 조건: 높은 카페인 또는 늦은 섭취 + 낮은 수면
        if risk == "높음":
            reasons.append("카페인 위험도: 높음")
        if late_flag and isinstance(sleep, (int, float)) and sleep < CONFIG["LOW_SLEEP"]:
            reasons.append("늦은 섭취 & 수면 부족")
        if (risk == "높음") or (late_flag and isinstance(sleep, (int, float)) and sleep < CONFIG["LOW_SLEEP"]):
            status = "위험형"
        else:
            # 주의형 조건
            if isinstance(caffeine, int) and caffeine >= CONFIG["HIGH_CAFFEINE"]:
                reasons.append(f"카페인 과다: {caffeine}잔")
            if isinstance(focus, int) and focus < CONFIG["LOW_FOCUS"]:
                reasons.append(f"낮은 집중도: {focus}")
            if isinstance(sleep, (int, float)) and sleep < 7:
                reasons.append(f"수면 부족: {sleep}h")

            if any(r for r in reasons if r not in ("불충분 입력: ",)) and status != "위험형":
                # 위험형이 아니고 주의 항목이 있으면 주의형
                status = "주의형" if reasons else status

        reason_text = "; ".join(reasons) if reasons else "근거 없음"

        classified.append({**record, "status": status, "reason": reason_text})

    return classified


def write_output(classified: list[dict]) -> str:
    """분류 결과를 읽기 쉬운 문장으로 정리한다."""
    lines = ["# StudyCaffeine Agent 결과", ""]

    for index, item in enumerate(classified, start=1):
        lines.append(f"## 기록 {index}")
        lines.append(f"- 상태: {item.get('status')}")
        lines.append(f"- 카페인 섭취량: {item.get('caffeine_amount')}잔")
        lines.append(f"- 마지막 섭취 시간: {item.get('last_caffeine_time')}")
        lines.append(f"- 집중도: {item.get('focus_score')}")
        sh = item.get('sleep_hours')
        lines.append(f"- 수면 시간: {sh}시간")
        # 판단 근거 추가
        reason = item.get("reason")
        if reason:
            lines.append(f"- 판단 근거: {reason}")

        if item["status"] == "건강형":
            lines.append("- 피드백: 현재 패턴을 유지하세요.")
        elif item["status"] == "주의형":
            lines.append("- 피드백: 카페인 섭취 시간과 수면 시간을 조금 더 조절하세요.")
        else:
            lines.append("- 피드백: 늦은 카페인을 줄이고 수면 회복을 우선하세요.")

        lines.append("")

    # 요약 계산 (안전하게 계산)
    n = len(classified) or 1
    total_caf = sum(item.get('caffeine_amount') if isinstance(item.get('caffeine_amount'), int) else 0 for item in classified)
    total_focus = sum(item.get('focus_score') if isinstance(item.get('focus_score'), int) else 0 for item in classified)
    total_sleep = sum(item.get('sleep_hours') if isinstance(item.get('sleep_hours'), (int, float)) else 0 for item in classified)

    lines.append("## 전체 요약")
    lines.append(f"- 평균 카페인 섭취량: {total_caf / n:.1f}잔")
    lines.append(f"- 평균 집중도: {total_focus / n:.1f}")
    lines.append(f"- 평균 수면 시간: {total_sleep / n:.1f}시간")

    return "\n".join(lines)


def save_result(classified: list[dict], filename: str = "caffeine_report.md") -> Path:
    """분류 결과를 Markdown 파일로 저장하고 저장된 Path를 반환한다.

    - 입력: `classify_items()`의 반환값(리스트)
    - 출력: 저장된 파일의 `pathlib.Path` 객체
    """
    content = write_output(classified)
    path = Path(filename)
    # UTF-8로 덮어쓰기
    path.write_text(content, encoding="utf-8")
    return path


def save_markdown_table(facts: list[dict], filename: str = "output.md") -> Path:
    """중간 정보(dict list)를 받아 Markdown 표로 `filename`에 저장하고 Path를 반환합니다.

    - 입력: `extract_facts()`가 반환한 리스트(중간 정보)
    - 출력: `pathlib.Path` 객체
    """
    path = Path(filename)

    # 표에 사용할 열(에이전트 주제에 맞는 key)
    columns = [
        "caffeine_amount",
        "last_caffeine_time",
        "focus_score",
        "sleep_hours",
        "sleep_status",
        "caffeine_risk",
    ]

    # 헤더 작성
    header = "| " + " | ".join(columns) + " |\n"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |\n"

    rows = []
    for item in facts:
        cells = []
        for col in columns:
            val = item.get(col, "")
            # 표현 정리
            if isinstance(val, float):
                cell = f"{val:.1f}"
            else:
                cell = str(val)
            cells.append(cell)
        rows.append("| " + " | ".join(cells) + " |\n")

    content = header + sep + "".join(rows)

    path.write_text(content, encoding="utf-8")
    return path


def review_guides_with_rules(guides: str) -> str:
    """간단 체크리스트로 `guides` 문자열을 검토하고 보고서를 반환합니다.

    검사 항목(간단한 규칙 기반):
    - 핵심 정보 누락: '카페인', '수면', '집중' 언급 여부
    - 대상 불분명: '학생/학습자/수강생/대상/사용자' 언급 여부
    - 단정 표현 사용: '무조건/반드시/절대/항상' 등

    복잡한 AI 판단은 하지 않고 단순 텍스트 체크만 수행합니다.
    """
    text = (guides or "").strip()
    lines: list[str] = ["# Review Report", ""]

    # 핵심 정보 검사
    core_keywords = ["카페인", "수면", "집중", "집중도", "섭취"]
    if not any(k in text for k in core_keywords):
        lines.append("- [ ] 핵심 정보 누락: '카페인/수면/집중' 관련 언급이 없습니다.")
    else:
        lines.append("- [x] 핵심 정보 포함: '카페인/수면/집중' 관련 언급이 확인되었습니다.")

    # 대상(타겟) 검사
    target_keywords = ["학생", "학습자", "수강생", "대상", "사용자", "본인"]
    if not any(k in text for k in target_keywords):
        lines.append("- [ ] 대상 불분명: 안내의 대상(예: 학생, 학습자 등)이 명확하지 않습니다.")
    else:
        lines.append("- [x] 대상 명시 여부: 대상 언급이 확인되었습니다.")

    # 단정 표현 검사
    absolutes = ["무조건", "반드시", "절대", "항상"]
    found_absolutes = [w for w in absolutes if w in text]
    if found_absolutes:
        lines.append(f"- [ ] 단정 표현 사용: {', '.join(found_absolutes)} 같은 단정어가 사용되었습니다.")
    else:
        lines.append("- [x] 단정 표현 없음: 공격적/절대적 단정어가 감지되지 않았습니다.")

    # 권장사항의 구체성(숫자/시간 등 포함 여부)
    if re.search(r"\d", text):
        lines.append("- [x] 구체성: 권장사항에 숫자/시간 등의 구체적 언급이 포함되어 있습니다.")
    else:
        lines.append("- [ ] 구체성 부족: 권장사항이 구체적 수치(예: 시간/잔수)를 포함하지 않습니다.")

    lines.append("")
    lines.append("참고: 이 검토는 단순 키워드 기반 체크리스트입니다. 추가 검토가 필요할 수 있습니다.")

    return "\n".join(lines)


def review_guides_with_groq(guides: str) -> str:
    """Groq API를 사용해 `guides`를 검토하고 체크리스트 보고서를 반환합니다.

    - `GROQ_API_KEY` 환경변수에서 키를 읽는다.
    - 호출 실패, 파싱 실패, 키 부재 시 예외를 올린다.
    - 상위 `review_guides()`에서 규칙 기반으로 폴백한다.
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY가 없습니다")

    prompt = {
        "guides": guides,
        "instructions": [
            "입력 자료에 없는 내용을 단정했는가",
            "핵심 정보가 빠졌는가",
            "사용자가 해야 할 일이 보이는가",
            "위험한 표현이 있는가",
        ],
        "output_format": "마크다운 체크리스트 4~6개와 짧은 한 줄 요약",
    }

    payload = json.dumps(
        {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You review guide text and return a concise markdown checklist in Korean.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "temperature": 0,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Groq 응답 내용이 비어 있습니다")
        return content.strip()
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Groq 검토 실패: {exc}") from exc


def review_guides(guides: str) -> str:
    """환경변수 설정에 따라 Groq 검토 또는 규칙 기반 검토를 실행합니다."""
    if USE_LLM_REVIEW:
        try:
            print("LLM 검토 시도: Groq")
            return review_guides_with_groq(guides)
        except Exception:
            print("LLM 검토 실패, 규칙 기반 검토로 전환")
            return review_guides_with_rules(guides)

    return review_guides_with_rules(guides)


def main() -> None:
    external_context = fetch_external_context(SAMPLE_INPUT)
    facts = analyze_input(SAMPLE_INPUT, external_context=external_context)
    classified = classify_items(facts)
    output = write_output(classified)

    print("=== extract_facts (중간정보) ===")
    print(json.dumps(facts, ensure_ascii=False, indent=2))
    print()

    print("=== classify_items 결과 ===")
    print(json.dumps(classified, ensure_ascii=False, indent=2))
    print()

    print("=== write_output 결과 ===")
    print(output)
    # 저장 및 저장된 파일 경로 출력
    saved_path = save_result(classified, "caffeine_report.md")
    print(f"저장 완료: {saved_path}")

    # 중간 정보(facts)를 Markdown 표로 저장
    table_path = save_markdown_table(facts, "output.md")
    print(f"표 저장 완료: {table_path}")

    # 생성된 가이드 텍스트를 간단히 검토하고 보고서를 저장
    review = review_guides(output)
    print("=== review_guides 결과 ===")
    print(review)
    review_path = Path("review_report.md")
    review_path.write_text(review, encoding="utf-8")
    print(f"검토 보고서 저장: {review_path}")


if __name__ == "__main__":
    main()
