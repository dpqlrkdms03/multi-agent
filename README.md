# StudyCaffeine Agent

## 한 문장 설명
사용자의 카페인 섭취량, 섭취 시간, 집중도 및 수면 시간을 입력받아 학습 습관 개선을 위한 맞춤형 피드백과 종합 통계 분석 보고서를 제공하는 AI 에이전트입니다.

## 해결하려는 문제
현대 학습자들이 겪는 무분별하고 늦은 시간의 카페인 섭취로 인한 수면 부족 및 집중도 저하의 악순환을 예방하고자 합니다. 사용자의 비정형 일지 데이터를 분석하여 건강한 학습 습관 형성을 정량적으로 트래킹하고 개선을 돕습니다.

## 실행 방법
```bash
# 기본 실행 (sample_input.txt 파일 감지 및 로드)
python my_agent.py

# 대화형 모드 실행 (터미널에서 직접 수동 입력)
python my_agent.py --interactive

# [선택] Groq API 기반의 LLM 분석 및 검토 기능을 활성화하여 실행
USE_LLM=True USE_LLM_REVIEW=True GROQ_API_KEY="your_api_key" python my_agent.py
```

## 입력 파일
- **[sample_input.txt](file:///c:/multi-agent/sample_input.txt)**: 사용자의 일별 카페인 섭취 및 학습 일지가 작성된 비정형 데이터 파일입니다.
  - 지원 시간 형식: `14:00`, `오후 2시`, `2:00 PM`, `14시 30분` 등
  - 지원 수면 시간 형식: `8시간`, `8h`, `7.5시간`, `6시간 30분` 등

## 출력 파일
- **[output.md](file:///c:/multi-agent/output.md)**: 사실 추출 에이전트가 파싱한 정보를 일목요연하게 구조화한 마크다운 데이터 표입니다.
- **[output_user_guide.md](file:///c:/multi-agent/output_user_guide.md)**: 각 일자별 카페인 위험도 분류 결과, 판단 근거, 맞춤형 생활 피드백 및 전체 데이터에 대한 평균/표준편차, 전후반 추세 분석(상승/하락)을 담은 종합 생활 습관 개선 리포트입니다. (하위 호환을 위해 `caffeine_report.md`도 동일 내용으로 복사본이 생성됩니다.)
- **[review_report.md](file:///c:/multi-agent/review_report.md)**: 최종 생성된 보고서의 신뢰도와 타당성을 자가 검증(핵심 단어 포함 여부, 대상 지정 여부, 강압적 단정 표현 사용 여부 등)하여 기록한 검토자 보고서입니다.

## 에이전트 역할
| 역할 | 함수 | 설명 |
|---|---|---|
| **사실 추출 에이전트 (Fact Extractor)** | [extract_facts](file:///c:/multi-agent/my_agent.py#L168) | 비정형 기록 문장을 정규 표현식으로 스캔하여 카페인 섭취량, 마지막 섭취 시간, 집중도, 수면 시간을 파싱하고 정규화합니다. |
| **상태 분류 에이전트 (Classifier)** | [classify_items](file:///c:/multi-agent/my_agent.py#L318) | 파싱된 데이터를 중앙 설정(`CONFIG`) 기준치와 비교하여 사용자의 생활 유형을 건강형, 주의형, 위험형으로 분류하고 세부 근거를 수집합니다. |
| **피드백 작성 에이전트 (Report Writer)** | [write_output](file:///c:/multi-agent/my_agent.py#L385) | 각 생활 등급별 맞춤형 피드백을 작성하고 전체 데이터의 수학적 통계(평균/표준편차/상승·하락 추세) 분석을 리포트로 구성합니다. |
| **검토자 에이전트 (Reviewer)** | [review_guides](file:///c:/multi-agent/my_agent.py#L646) | 완성된 보고서에 핵심 정보가 누락되었거나 지나치게 단정적인 언어 사용이 감지되는지를 체크리스트 기반으로 자가 진단합니다. |

## 사용한 코딩에이전트
- **GitHub Copilot**: 초기 정규식 파서 함수 및 시간 전처리 헬퍼 함수의 자동완성과 디버깅에 활용
- **Antigravity (Gemini)**: 코파일럿 학생 크레딧 소진 이후에 투입되어, 전체 코드 구조 분석(학습 리포트 작성), 제출 파일 리스트 정비, 비정형 sample_input.txt 파일 입력 연동 개선 및 발표자료와 최종 문서화 작업을 안전하게 완수

## 구현 수준
- 기본형 / 중급형 / 확장형 / 심화형: **중급형** (다단계 규칙 기반 의사결정 분류, 이중 백업 파일 저장, 분리된 외부 Context 연동 및 표준편차/추세 분석 통계 기능 내장)

## 사용한 API 또는 외부 도구
- 없음 / Groq API / 외부 API / LangGraph: **Groq API** (선택적 사용)
  - **필요 환경변수**:
    - `USE_LLM`: `True` 설정 시 Groq Llama-3.1-8b 모델을 활용한 사실 분석 수행
    - `USE_LLM_REVIEW`: `True` 설정 시 Groq API를 활용해 생성된 피드백의 자가 검토 기능 활성화
    - `GROQ_API_KEY`: Groq API 인증을 위한 API 키
  - **Fallback(대체) 동작**:
    - 해당 환경변수가 설정되지 않았거나 키가 누락된 경우, 혹은 API 호출 중 타임아웃이나 오류가 발생하면 즉시 예외 처리를 거쳐 내장된 자체 규칙 기반 분석 로직([analyze_with_rules](file:///c:/multi-agent/my_agent.py#L290)) 및 규칙 기반 자가 검토 로직([review_guides_with_rules](file:///c:/multi-agent/my_agent.py#L540))으로 자동 Fallback(폴백)되어 에러 없이 분석을 완료합니다.

## 현재 한계
- **비정형 자연어 파싱 의존성**: 정규 표현식으로 전처리를 수행하므로, "커피 한 사발", "몬스터 반 캔"과 같이 수치와 단위가 불분명하거나 크게 변형된 텍스트는 정확한 수치를 추출하지 못하고 `'확인 필요'` 태그로 분류됩니다.
- **배치 형태의 수동 구동**: 사용자가 실시간 대시보드나 모바일 UI에서 트래킹하는 것이 아닌, 터미널 실행을 통한 정적 마크다운 보고서 생성으로 제한되어 있습니다.
