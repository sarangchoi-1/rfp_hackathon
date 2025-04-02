# Agent 모듈

## 개요
Agent 모듈은 RFP(제안요청서) 분석을 위한 지능형 시스템의 핵심 컴포넌트입니다. 사용자의 요청을 이해하고, 체계적으로 분석하여 구조화된 결과를 도출합니다.

## 주요 기능
1. **작업 분해 (Task Decomposition)**
   - 사용자의 요청을 작은 단위의 작업으로 분해
   - 각 작업에 우선순위와 의존성 부여
   - 작업 간의 관계 구조화

2. **카테고리 매칭 (Category Matching)**
   - 의료/금융 도메인 특화 카테고리 분류
   - 텍스트 분석을 통한 관련성 점수 계산
   - 다중 카테고리 매칭 지원

3. **결과 구성 (Result Composition)**
   - 분류된 작업들의 통합적 분석
   - 구조화된 결과 도출
   - 최종 보고서 생성

## 디렉토리 구조
```
agent/
├── core/                    # 핵심 처리 모듈
│   ├── task_decomposer.py   # 작업 분해기
│   ├── category_matcher.py  # 카테고리 매칭기
│   └── result_composer.py   # 결과 구성기
├── memory/                  # 메모리 시스템
│   ├── short_term.py       # 단기 기억 관리
│   ├── long_term.py        # 장기 기억 관리
│   └── working.py          # 작업 기억 관리
└── __init__.py             # 패키지 초기화
```

## 메모리 시스템
1. **단기 기억 (Short-term Memory)**
   - 최근 작업 컨텍스트 저장
   - 임시 데이터 관리
   - 작업 흐름 추적

2. **장기 기억 (Long-term Memory)**
   - 과거 작업 결과 저장
   - 패턴 학습 및 활용
   - 성과 데이터 관리

3. **작업 기억 (Working Memory)**
   - 현재 처리 중인 작업 관리
   - 임시 계산 결과 저장
   - 작업 상태 추적

## 카테고리 시스템
현재 지원되는 주요 카테고리:
- **의료 (Medical)**: 의료 시스템, 환자 관리, 진료 프로세스 등
- **금융 (Finance)**: 금융 서비스, 투자 관리, 보험 시스템 등
- **규제 준수 (Compliance)**: HIPAA, GDPR 등 규제 준수
- **기술 (Technology)**: 시스템 아키텍처, 보안, 인프라 등
- **운영 (Operations)**: 프로세스 관리, 품질 관리, 서비스 운영 등

## 사용 예시
```python
# 작업 분해 예시
task_decomposer = TaskDecomposer()
tasks = task_decomposer.decompose_request("의료 정보 시스템 보안 강화 프로젝트")

# 카테고리 매칭 예시
category_matcher = CategoryMatcher()
categories = category_matcher.match_task_to_categories(tasks[0])

# 결과 구성 예시
result_composer = ResultComposer()
final_result = result_composer.compose_result(tasks, categories)
```

## 의존성
- Python 3.8 이상
- scikit-learn (텍스트 분석용)
- numpy (수치 계산용)

## 주의사항
1. 메모리 시스템은 순차적으로 초기화되어야 합니다.
2. 카테고리 매칭은 한국어와 영어를 모두 지원합니다.
3. 작업 분해 시 의존성 순환을 주의해야 합니다. 