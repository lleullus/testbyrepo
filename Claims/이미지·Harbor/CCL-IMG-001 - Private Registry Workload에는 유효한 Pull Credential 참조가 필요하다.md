---
type: conditional-claim
claim_id: CCL-IMG-001
claim_kind: rule
domain: image-and-registry

decision_question: "Private Registry 이미지가 401·403 또는 ImagePullBackOff로 실패할 때 어떤 인증 구성을 확인하는가?"
derivation: repeated

evidence_status: supported
currentness: unverified-current
operational_use: advisory

service_models: [unknown]
network_profiles: [unknown]
directions: [outbound]
purposes: [private-registry-image-pull]
protocols: [https]

evidence_ids:
  - "2026020210355795480"
  - "2026050711103676786"
  - "2026032015044075665"
evidence_first_seen: 2026-02-02
evidence_last_seen: 2026-05-07

source_fidelity_min: full-dialogue
depends_on: []
supersedes: []
superseded_by: []
last_reviewed: 2026-09-25
---

# Claim

Private Registry 이미지를 Pull하는 Pod·CronJob에는 유효한 Registry Credential이 Secret 또는 ServiceAccount를 통해 연결되어야 하며, 해당 참조가 누락되거나 Secret 데이터가 잘못되면 401·403과 Image Pull 실패가 발생할 수 있다.

## 판단 질문

> Registry에 이미지는 있는데 Pod가 401·403 또는 ImagePullBackOff로 시작하지 못하는 이유는 무엇인가?

## 적용 조건

- 이미지가 인증이 필요한 Private Registry에 있음
- Pod Event에 401, 403, Unauthorized, Forbidden 또는 ImagePullBackOff가 나타남
- Image 이름·Tag가 실제로 존재함을 별도로 확인함

## 적용 전 확인할 미지수

- PodSpec 또는 ServiceAccount가 참조하는 `imagePullSecrets`
- Secret의 `.dockerconfigjson` Registry Host·ID·Password·Token
- Image Reference가 Registry·Repository·Tag 전체 경로인지
- Registry Network·TLS Trust가 정상인지

## 근거 사슬

1. 2026-02 사례에서 운영팀은 Image Pull 문제의 첫 점검으로 Pull Secret의 Docker Config 데이터를 Decode해 ID·Password·Token을 검증하도록 했다.
2. 같은 사례는 Registry Host만이 아니라 Image 전체 경로를 명시하도록 했다.
3. 2026-05 CronJob 사례는 Manifest의 `imagePullSecrets` 누락이 401의 직접 원인이었다.
4. 2026-03 사례도 403 발생 시 Pod가 참조하는 Pull Secret의 Credential을 갱신하도록 했다.
5. 따라서 Private Registry Pull 성공에는 Workload에 연결된 유효 Credential과 올바른 Image Reference가 필요하다는 Claim이 지지된다.

## 근거표

| 관계 | VOC | 자료 상태 | 직접 확인된 사실 | 근거 파일·행 |
|---|---|---|---|---|
| direct-support | 2026020210355795480 | full-dialogue | Pull Secret의 Docker Config ID·Password·Token과 전체 Image 경로를 점검한다. | `VOC/2026-02-01 ~ 2026-02-07 DKS VOC 목록 (23건).md` 948-987행 |
| direct-support | 2026050711103676786 | full-dialogue | CronJob Manifest의 `imagePullSecrets` 누락으로 401이 발생했다. | `VOC/2026-05-03 ~ 2026-05-09 DKS VOC 목록 (6건).md` 129-137행 |
| corroboration | 2026032015044075665 | full-dialogue | 403 발생 시 최신 Credential로 Pull Secret을 재발급·갱신하도록 했다. | `VOC/2026-03-15 ~ 2026-03-21 DKS VOC 목록 (12건).md` 155-162행 |

## 이 Claim이 말하지 않는 것

- 모든 ImagePullBackOff가 인증 문제라는 뜻이 아니다.
- Pull Secret만 올바르면 Registry Network·DNS·CA Trust가 정상이라는 뜻이 아니다.
- 모든 Workload가 PodSpec에 Secret을 직접 적어야 한다는 뜻이 아니다. ServiceAccount 기본 참조가 있을 수 있다.

## 반례·경쟁 설명

- 존재하지 않는 Tag, 잘못된 Image Path, Registry Rate Limit, Network Timeout, CA 오류도 유사 증상을 만든다.
- 공개 Image 또는 Node Credential Provider를 사용하는 환경은 별도 Pull Secret이 필요하지 않을 수 있다.

## 무효화 조건

- DKS가 Workload별 Secret 없이 Registry Identity를 자동 주입하는 공식 인증 방식으로 전환하면 적용 범위를 수정한다.

## 다음 검증

- 현재 DKS-N·DKS-C의 기본 ServiceAccount Pull Secret 자동 연결 여부와 Harbor Robot Account 권장 방식을 확인한다.

## 하위 문서 사용 조건

- 401·403 Image Pull 오류의 인증 분기에는 사용할 수 있다.
- Credential 수명주기는 [[CCL-IMG-002 - Registry Credential 변경 시 Pull Secret을 갱신해야 한다]]를 함께 적용한다.
