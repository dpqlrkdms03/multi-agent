import re
from pathlib import Path
from typing import Any, Dict, List


SAMPLE_FILE = "sample_notices.txt"


def load_notices(path: str = SAMPLE_FILE) -> List[str]:
    """입력 파일을 읽고 공지 블록 리스트로 분리한다."""
    p = Path(path)
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8").strip()
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def normalize_date(date_str: str) -> str:
    """표시용 날짜 문자열을 정리한다 (없으면 빈 문자열)."""
    return (date_str or "").replace("일시:", "").strip()


def extract_facts(notice: str) -> Dict[str, Any]:
    """사실 추출 에이전트: 제목/일시/대상/행동/준비물 추출."""
    lines = [l.strip() for l in notice.splitlines() if l.strip()]
    title = "(제목 없음)"
    if lines:
        title = re.sub(r"^\[공지\]\s*", "", lines[0]).strip() or "(제목 없음)"

    date = ""
    target = ""
    content_lines: List[str] = []
    for l in lines[1:]:
        if l.startswith("일시:"):
            date = l.split("일시:", 1)[1].strip()
        elif l.startswith("대상:"):
            target = l.split("대상:", 1)[1].strip()
        elif l.startswith("내용:"):
            content_lines.append(l.split("내용:", 1)[1].strip())
        else:
            content_lines.append(l)

    content = " ".join(content_lines)

    items: List[str] = []
    item_match = re.search(r"(?:준비물|지참(?:하세요|해 주세요)?)\s*[:：]?\s*([^\.\n]+)", content)
    if item_match:
        items = [x.strip() for x in re.split(r"[,/，]\s*", item_match.group(1)) if x.strip()]

    task = ""
    for keyword in ["제출", "신청", "참석", "모집", "발표", "준비"]:
        if keyword in content:
            task = keyword
            break

    return {
        "title": title,
        "date": normalize_date(date),
        "target": target,
        "task": task,
        "items": items,
        "raw": notice,
    }


def classify_schedule(facts_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """일정 분류 에이전트: 대상 문구를 기준으로 공지를 묶는다."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for f in facts_list:
        target = (f.get("target") or "대상 불명확").strip()
        if "전체" in target:
            key = "전체 학생"
        elif "1학년" in target:
            key = "1학년"
        elif "2학년" in target:
            key = "2학년"
        elif "3학년" in target:
            key = "3학년"
        elif "4학년" in target:
            key = "4학년"
        else:
            key = target
        groups.setdefault(key, []).append(f)
    return groups


def write_output(facts_list: List[Dict[str, Any]], path: Path = Path("output.md")) -> Path:
    """공지 표를 저장한다."""
    lines = [
        "# 공지 요약",
        "",
        "| 제목 | 대상 | 날짜 | 해야 할 일 | 준비물 |",
        "|---|---|---|---|---|",
    ]
    for f in facts_list:
        items_text = ", ".join(f.get("items") or [])
        task_text = f.get("task") or ""
        lines.append(
            f"| {f.get('title', '')} | {f.get('target', '')} | {f.get('date', '')} | {task_text} | {items_text} |"
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_user_guide(grouped: Dict[str, List[Dict[str, Any]]], path: Path = Path("output_user_guide.md")) -> Path:
    """안내문 작성 에이전트: 대상 그룹별 안내문을 저장한다."""
    lines = ["# 사용자별 안내문", ""]
    for group, items in grouped.items():
        lines.append(f"## {group}")
        for it in items:
            when = it.get("date") or "날짜 미상"
            task = it.get("task") or "확인 필요"
            prep = ", ".join(it.get("items") or []) or "없음"
            lines.append(f"- {it.get('title', '(제목 없음)')}: {when} / 해야 할 일: {task} / 준비물: {prep}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def review_output(facts_list: List[Dict[str, Any]], path: Path = Path("review_report.md")) -> Path:
    """검토자 에이전트: 누락 필드 점검 리포트를 저장한다."""
    issues: List[str] = []
    for idx, fact in enumerate(facts_list, 1):
        if not fact.get("date"):
            issues.append(f"- 공지 {idx}: 날짜 누락 ({fact.get('title', '(제목 없음)')})")
        if not fact.get("target"):
            issues.append(f"- 공지 {idx}: 대상 누락 ({fact.get('title', '(제목 없음)')})")

    lines = ["# Review Report", "", f"총 공지 수: {len(facts_list)}"]
    if issues:
        lines.append("검토 결과: 보완 필요")
        lines.append("")
        lines.append("## 이슈 목록")
        lines.extend(issues)
    else:
        lines.append("검토 결과: 주요 필드 모두 존재")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    notices = load_notices(SAMPLE_FILE)
    if not notices:
        print(f"입력 파일을 찾지 못했습니다: {SAMPLE_FILE}")
        return

    # 1) 사실 추출 에이전트
    facts = [extract_facts(n) for n in notices]
    # 2) 일정 분류 에이전트
    grouped = classify_schedule(facts)
    # 3) 안내문 작성 에이전트
    output_path = write_output(facts)
    guide_path = write_user_guide(grouped)
    # 4) 검토자 에이전트
    review_path = review_output(facts)

    print("== 공지 처리 결과 요약 ==")
    print(f"총 공지 수: {len(facts)}")
    print(f"출력 파일 생성: {output_path.name}, {guide_path.name}, {review_path.name}")


if __name__ == "__main__":
    main()
