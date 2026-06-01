# Week10 Tool Practice

이번 문서는 10주차 실습에서 사용하는 도구별 연습 절차를 간단히 정리합니다. 목표는 도구별 작업 흐름을 익히고, 같은 작업을 서로 다른 도구로 지시해 본 뒤 결과 차이를 비교하는 것입니다.

## 목표

- GitHub Copilot, Gemini CLI, Antigravity의 기본 사용 흐름을 익힌다.
- Playwright CLI로 HTML 미리보기를 확인한다.

## 절차 요약

1. 컨텍스트 제공: `AGENTS.md`, `context.md`, `todo.md`를 읽힌다.
2. 계획 요청: 변경 전에 작업 계획(단계)를 요청한다.
3. 계획 검토: 계획을 확인하고 승인한다.
4. 실행 요청: 승인한 계획에 따라 파일을 수정하게 한다.
5. 변경 확인: 수정된 파일과 실행 결과를 검토한다.

## 도구별 예시

- GitHub Copilot: VS Code 내에서 `context.md`와 `todo.md`를 읽히고 문서 초안을 만들게 한다.
- Gemini CLI: 터미널에서 `gemini` 실행 후, 먼저 파일을 읽고 5단계 계획만 제시하게 한다.
- Antigravity: Agent Manager로 작업을 세분화하고 단계별로 검토한다.

## Playwright CLI 사용 예시

```powershell
npm install -g @playwright/cli@latest
playwright-cli install-browser
playwright-cli open docs/week-10.html
```

## 확인 사항

- 도구가 제안한 변경이 프로젝트 범위를 벗어나지 않는지 확인합니다.
- 외부 패키지나 민감 정보(API 키 등)가 코드에 포함되지 않았는지 확인합니다.

---

간단한 실습 가이드로 사용하세요. 더 상세한 템플릿이나 예시가 필요하면 알려주세요.
