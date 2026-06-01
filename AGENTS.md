# AGENTS.md

이 파일은 GitHub Copilot, Gemini CLI, Antigravity에서 공통으로 참고할 프로젝트 규칙이다. 무료 사용량이 남아 있는 도구를 번갈아 쓰더라도 같은 규칙으로 작업한다.

## 프로젝트

# AGENTS.md

이 파일은 GitHub Copilot, Gemini CLI, Antigravity에서 공통으로 참고할 프로젝트 규칙이다.

## 프로젝트

- 이름: 일정공지 에이전트
- 기본 실행: `python schedule_agent.py`
- 기본 작업 파일: `schedule_agent.py`

## 작업 방식

1. 파일을 수정하기 전에 먼저 계획을 제시한다.
2. 한 번에 많은 파일을 바꾸지 않는다.
3. 오류가 나면 새 기능을 추가하지 말고 오류만 고친다.
4. 변경 후 실행 명령과 확인 결과를 보고한다.

## 금지

- 불필요한 패키지 설치
- API 키 하드코딩
- 복잡한 프레임워크 임의 추가
- Playwright MCP 연결
