---
title: "DEV·PRD Member ks-apiserver SECDS T2 CA Bundle 적용 작업계획서"
created: "2026-08-19"
updated: "2026-08-19"
status: draft
document_type: plan-note
schema_version: 1
project: "Xi'an 전환 운영 가이드"
owner: "원문 미기재"
reviewer: "원문 미기재"
plan_type: operation-workplan
priority: "원문 미기재"
tags:
  - workplan
  - operations
  - 작업계획서
  - kubesphere
  - harbor
  - x509
  - certificate
  - ca
related:
  - "[[50. 운영/04. Kubesphere Operation/07. KubeSphere SECDS-ROOT.crt ConfigMap Mount|KubeSphere SECDS-ROOT.crt ConfigMap Mount]]"
  - "[[30. 구축 및 전환/공통 구축/Xi'an/한국어/02. K8S Cluster Nodes Pre-setting|K8S Cluster Nodes Pre-setting]]"
  - "[[50. 운영/07. DKS User Guide/03. KubeSphere User Guide|KubeSphere User Guide]]"
version: 0.1
source: "사용자 제공 openssl s_client -showcerts 출력(2026-08-19) 및 Xi'an 전환 운영 가이드"
doc_status: "계획 초안"
---

# DEV·PRD Member ks-apiserver SECDS T2 CA Bundle 적용 작업계획서

> [!warning] 문서 상태
> 사용자 제공 `openssl s_client -showcerts` 출력과 Xi'an 운영 가이드를 기준으로 작성한 실행 전 계획이다. DEV Member 검증이 완료되기 전에는 PRD Member 작업에 진입하지 않으며, 실행 증적이 기록되기 전에는 작업 완료로 간주하지 않는다.

## [ 작업 개요 ]

| 항목 | 내용 |
| --- | --- |
| 작업 일정 | 결정 전 확인 필요 |
| 작업자 / 검증자 | 원문 미기재 / 원문 미기재 |
| 작업 내용 | `dev-apps-pa01-xas`와 `prd-apps-pa01-xas`의 `kubesphere-system/ks-apiserver`가 Harbor 인증서 체인을 검증할 수 있도록 별도 `secds-t2-ca` ConfigMap의 `ca.crt`에 `SECDS-T2IssuingCA` + `SECDS-T2ROOTCA` CA bundle을 등록하고, `ks-apiserver`의 인증서 디렉터리에 단일 파일로 추가 마운트한다. DEV를 먼저 적용·검증한 뒤 PRD에 동일 적용한다. |
| 작업 목적 | KubeSphere `Creating a Deployment → Add Container`에서 `xa.dcr.dks.samsungds.net/...` 이미지 경로 입력 시 DEV Member `ks-apiserver`에서 확인된 `x509: certificate signed by unknown authority` 오류를 해소한다. |
| 작업 대상 및 범위 | 포함: `dev-apps-pa01-xas`, `prd-apps-pa01-xas`의 `kubesphere-system/ks-apiserver`, 신규 `secds-t2-ca` ConfigMap. 제외: 기존 `secds-rootca` ConfigMap, `prd-host-pa01-xas`, Harbor/LB 인증서 설정, Worker Node container runtime trust 설정. |
| 예상 영향 | 각 Member의 `ks-apiserver` 재기동/rollout 동안 해당 Member에 대한 KubeSphere API 기능이 일시적으로 영향을 받을 수 있다. 애플리케이션 Workload 자체는 이번 계획의 직접 변경 대상이 아니다. 실제 영향은 작업 중 확인한다. |
| 작업 방식 | 승인된 T2 CA 확인 → 현재 설정 백업 → DEV Member CA bundle 적용 → DEV UI/로그 검증 → 성공 시 PRD Member 동일 적용 → 양쪽 최종 검증 순으로 수행한다. |

### 작업 판단

사용자 제공 Harbor TLS 확인 결과에서 서버가 `-showcerts`로 직접 제공한 `Certificate chain`은 `0`번 `xa.dcr.dks.samsungds.net` 서버 인증서 1장뿐이다. 서버 인증서의 Issuer는 `SECDS-T2IssuingCA`이고, 동일 출력에서 검증 경로는 `depth=1 SECDS-T2IssuingCA`, `depth=2 SECDS-T2ROOTCA`, 최종 `Verify return code: 0 (ok)`로 확인됐다.

즉 Bastion에서는 로컬 trust store를 통해 Issuing CA와 Root CA까지 체인이 완성되지만, DEV Member `ks-apiserver`에서는 동일 Harbor 접근 시 `x509: certificate signed by unknown authority`가 확인된 상태다. 기존 Xi'an 가이드는 이 오류가 발생하면 각 Member Cluster의 `kubesphere-system`에 사내 CA를 ConfigMap으로 등록하고 `ks-apiserver`에 마운트하도록 정의한다.

또한 Xi'an K8S Node Pre-setting 문서는 승인된 패키지에 추가 `SECDS-T2*` 인증서 파일이 있는지 확인하도록 명시한다. 따라서 이번 작업은 Harbor/LB를 변경하지 않고 기존 Member `ks-apiserver` CA 신뢰 메커니즘을 그대로 사용하되, `ca.crt`에 실제 T2 체인에 필요한 `SECDS-T2IssuingCA`와 `SECDS-T2ROOTCA`를 함께 포함하는 것을 최소 변경으로 한다.

PRD Member는 DEV Member와 동일한 구성이라는 사용자 확인을 기준으로 DEV 성공 후 동일 변경을 적용한다. Host Cluster는 이번 오류의 확인 대상이 아니므로 작업 범위에서 제외한다.

### 작업 전 필수 확인

1. 승인된 Xi'an 인증서 파일 중 Subject/CN이 각각 `SECDS-T2IssuingCA`, `SECDS-T2ROOTCA`인 인증서를 확인한다. 파일명만으로 인증서를 선택하지 않는다.
2. CA bundle에는 `SECDS-T2IssuingCA`와 `SECDS-T2ROOTCA`만 포함하고 `xa.dcr.dks.samsungds.net` 서버 인증서와 Private Key는 포함하지 않는다.
3. DEV/PRD 각각에서 `ks-apiserver` Deployment를 YAML로 백업하고, 기존 `secds-rootca` 또는 기타 사내 CA 마운트가 있는지 확인한다. 기존 설정은 수정하지 않는다.
4. DEV/PRD 각각의 작업 context가 대상 Member Cluster임을 확인한다. Host context에서는 본 작업을 수행하지 않는다.
5. DEV에서 현재 `Creating a Deployment → Add Container` 이미지 입력 시 발생하는 x509 오류와 `ks-apiserver` 로그를 작업 전 증적으로 남긴다.
6. `ks-apiserver` 컨테이너의 인증서 디렉터리를 직접 확인한다. `SSL_CERT_DIR`이 설정되어 있으면 첫 번째 지정 디렉터리를 사용하고, 설정되어 있지 않으면 `/etc/ssl/certs` 존재 여부를 확인한다. 사용할 디렉터리가 컨테이너에 없으면 패치하지 않고 중단한다.

승인된 Xi'an 패키지의 CA 파일 확인에는 기존 구축 문서의 다음 확인 절차를 사용한다.

```bash
find /app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0 -maxdepth 2 -name 'SECDS-*.crt' -print
```

Harbor가 서버 측에서 제공하는 체인은 사용자 제공 확인과 동일한 방식으로 작업 전 재확인할 수 있다.

```bash
openssl s_client \
  -connect xa.dcr.dks.samsungds.net:443 \
  -servername xa.dcr.dks.samsungds.net \
  -showcerts </dev/null
```

## [ 작업 순서 요약 ]

| Task | 단계 | 작업대상 | 작업 내용 | 검증 기준 | 서비스 영향 |
| --- | --- | --- | --- | --- | --- |
| 0-1 | 사전 작업 | T2 CA / DEV·PRD Member | 승인된 `SECDS-T2IssuingCA`, `SECDS-T2ROOTCA` 확인 및 CA bundle 준비 | 두 CA의 Subject/CN이 확인되고 서버 인증서·Private Key가 bundle에 포함되지 않음 | 없음 |
| 0-2 | 사전 작업 | DEV·PRD `ks-apiserver` | Deployment 백업, 인증서 디렉터리 및 기존 CA 마운트 확인 | 작업 전 상태와 실제 인증서 디렉터리 식별 가능 | 없음 |
| 1-1 | 본 작업 | DEV Member | 신규 `secds-t2-ca/ca.crt` 생성 후 `ks-apiserver` 인증서 디렉터리에 단일 파일 추가 마운트 | `ks-apiserver` rollout 완료, CA bundle 파일 2개 인증서 확인 | DEV KubeSphere API 일시 영향 가능 |
| 1-2 | 본 작업 | DEV Member | KubeSphere Add Container에서 Harbor 이미지 입력 재검증 | 신규 `unknown authority` 오류 없음 | 없음 |
| 1-3 | 본 작업 | PRD Member | DEV 성공 확인 후 동일 CA bundle 적용 및 `ks-apiserver` 재기동 | `ks-apiserver` rollout 완료, Pod 정상 | PRD KubeSphere API 일시 영향 가능 |
| 2-1 | 사후 작업 | DEV·PRD Member | 양쪽 UI/로그 및 적용 상태 최종 검증 | 두 Member 모두 Add Container 이미지 입력 시 x509 미발생 | 없음 |

## [ 작업 순서 ]

## 0. 사전 작업

### Task 0-1. T2 CA 확인 및 bundle 준비

1. 승인된 Xi'an 패키지에서 `SECDS-*.crt` 파일을 확인한다.
2. 실제 인증서 Subject/CN을 기준으로 `SECDS-T2IssuingCA`와 `SECDS-T2ROOTCA`를 식별한다.
3. `ca.crt`에 사용할 CA bundle은 `SECDS-T2IssuingCA`와 `SECDS-T2ROOTCA` 두 인증서를 함께 포함하도록 준비한다.
4. 서버 인증서 `CN=xa.dcr.dks.samsungds.net`과 Private Key가 bundle에 포함되지 않았는지 확인한다.

검증 기준: 적용할 두 CA가 사용자 제공 TLS 출력의 `depth=1 SECDS-T2IssuingCA`, `depth=2 SECDS-T2ROOTCA`와 일치해야 한다.

중단 조건: 승인된 Issuing CA 또는 Root CA를 식별할 수 없거나 인증서 출처가 승인된 Xi'an 자료인지 확인할 수 없으면 Member Cluster 변경을 시작하지 않는다.

### Task 0-2. 작업 전 상태 백업 및 대상 확인

1. DEV Member Bastion에서 현재 context와 `ks-apiserver` 상태를 확인한다.
2. `ks-apiserver` Deployment를 작업 전 YAML로 백업한다.
3. 실제 컨테이너 이름과 인증서 디렉터리를 확인한다.
4. 기존 사내 CA 관련 Volume/VolumeMount가 있더라도 이번 작업에서는 수정하지 않는다.

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl -n kubesphere-system rollout status deployment ks-apiserver

mkdir -p "$HOME/ks-apiserver-secds-t2-backup"
kubectl -n kubesphere-system get deployment ks-apiserver -o yaml \
  > "$HOME/ks-apiserver-secds-t2-backup/ks-apiserver.before.yaml"

kubectl -n kubesphere-system get deployment ks-apiserver \
  -o jsonpath='{.spec.template.spec.containers[*].name}{"\n"}'

kubectl -n kubesphere-system get deployment ks-apiserver -o yaml | \
  grep -nEi 'secds|rootca|ca\.crt|volumeMounts|volumes' || true

POD=$(kubectl -n kubesphere-system get pods -o name | \
  awk -F/ '/pod\/ks-apiserver-/{print $2; exit}')

echo "$POD"

kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  sh -c 'env | grep "^SSL_CERT_" || true; ls -ld /etc/ssl/certs'
```

`SSL_CERT_DIR`이 별도로 설정되어 있지 않으면 이번 작업의 `CERT_DIR`은 `/etc/ssl/certs`로 사용한다. `SSL_CERT_DIR`이 설정되어 있으면 해당 값의 첫 번째 디렉터리를 사용하고 실제 디렉터리 존재를 확인한다.

```bash
CERT_DIR=$(kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  sh -c 'if [ -n "$SSL_CERT_DIR" ]; then printf "%s\n" "$SSL_CERT_DIR" | cut -d: -f1; else printf "/etc/ssl/certs\n"; fi')

echo "$CERT_DIR"

kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  sh -c "test -d '$CERT_DIR' && ls -ld '$CERT_DIR'"
```

검증 기준: DEV context가 맞고, `ks-apiserver`가 정상이며, 컨테이너 이름 `ks-apiserver`와 사용할 `CERT_DIR`이 확인되어야 한다.

중단 조건: 대상 context가 DEV Member가 아니거나 `ks-apiserver`가 작업 전부터 비정상인 경우, 또는 사용할 인증서 디렉터리가 존재하지 않는 경우 본 작업에 진입하지 않는다.

## 1. 본 작업

### Task 1-1. DEV Member에 T2 CA bundle 적용

1. 승인된 Issuing CA와 Root CA 파일을 지정하고 bundle을 만든다.
2. Issuing CA가 Root CA로 검증되는지 확인한다.
3. 해당 bundle을 사용했을 때 Harbor TLS 검증이 성공하는지 확인한다.
4. 신규 `secds-t2-ca` ConfigMap을 생성한다.
5. 기존 trust store를 덮어쓰지 않고 `CERT_DIR/SECDS-T2-CA-BUNDLE.crt` 한 파일만 `ks-apiserver`에 추가 마운트한다.

```bash
ISSUING=/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2IssuingCA.crt
ROOT=/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2ROOTCA.crt
CA_BUNDLE=/tmp/SECDS-T2-CA-BUNDLE.crt

openssl x509 -in "$ISSUING" -noout -subject -issuer -fingerprint -sha256
openssl x509 -in "$ROOT" -noout -subject -issuer -fingerprint -sha256

cat "$ISSUING" "$ROOT" > "$CA_BUNDLE"

grep -c 'BEGIN CERTIFICATE' "$CA_BUNDLE"
openssl verify -CAfile "$ROOT" "$ISSUING"

openssl s_client \
  -connect xa.dcr.dks.samsungds.net:443 \
  -servername xa.dcr.dks.samsungds.net \
  -CAfile "$CA_BUNDLE" \
  -verify_return_error </dev/null 2>&1 | \
  grep 'Verify return code'
```

`grep -c` 결과는 `2`, `openssl verify`는 `OK`, Harbor 검증은 `Verify return code: 0 (ok)`여야 한다. 이 조건을 만족하지 않으면 Cluster를 변경하지 않는다.

ConfigMap을 생성한다. 동일 명령을 다시 실행해도 갱신할 수 있도록 `--dry-run=client -o yaml | kubectl apply -f -` 형태로 적용한다.

```bash
kubectl -n kubesphere-system create configmap secds-t2-ca \
  --from-file=ca.crt="$CA_BUNDLE" \
  --dry-run=client -o yaml | \
  kubectl apply -f -

kubectl -n kubesphere-system get configmap secds-t2-ca
```

Deployment 패치 파일을 만든다.

```bash
cat > /tmp/ks-apiserver-secds-t2-ca-patch.yaml <<EOF
spec:
  template:
    spec:
      volumes:
        - name: secds-t2-ca
          configMap:
            name: secds-t2-ca
            items:
              - key: ca.crt
                path: SECDS-T2-CA-BUNDLE.crt
      containers:
        - name: ks-apiserver
          volumeMounts:
            - name: secds-t2-ca
              mountPath: ${CERT_DIR}/SECDS-T2-CA-BUNDLE.crt
              subPath: SECDS-T2-CA-BUNDLE.crt
              readOnly: true
EOF

cat /tmp/ks-apiserver-secds-t2-ca-patch.yaml
```

`ks-apiserver`에 적용한다.

```bash
kubectl -n kubesphere-system patch deployment ks-apiserver \
  --type=strategic \
  --patch-file /tmp/ks-apiserver-secds-t2-ca-patch.yaml

kubectl -n kubesphere-system rollout status deployment ks-apiserver \
  --timeout=180s
```

패치 자체가 Pod template을 변경하므로 최초 적용 시 별도의 `rollout restart`는 필요하지 않다.

새 Pod에서 실제 마운트를 확인한다.

```bash
POD=$(kubectl -n kubesphere-system get pods -o name | \
  awk -F/ '/pod\/ks-apiserver-/{print $2; exit}')

kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  ls -l "${CERT_DIR}/SECDS-T2-CA-BUNDLE.crt"

kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  sh -c "grep -c 'BEGIN CERTIFICATE' '${CERT_DIR}/SECDS-T2-CA-BUNDLE.crt'"
```

검증 기준: DEV `ks-apiserver` rollout이 완료되고, 새 Pod에서 bundle 파일이 존재하며 인증서 개수가 `2`로 확인되어야 한다.

중단 조건: `ks-apiserver` rollout 실패, 새 Pod 비정상, bundle 파일 미마운트 또는 인증서 개수 불일치가 발생하면 PRD 작업으로 진행하지 않고 DEV 복구를 수행한다.

### Task 1-2. DEV Member 기능 검증 및 PRD 진입 판정

1. KubeSphere에서 DEV Member의 테스트 Project로 이동한다.
2. **Application Workloads → Workloads → Deployments → Create → Add Container**로 이동한다.
3. 기존에 오류가 발생했던 `xa.dcr.dks.samsungds.net/...` 이미지 경로를 동일하게 입력한다.
4. 입력 직후 모든 `ks-apiserver` Pod의 최근 로그에서 신규 x509가 발생하는지 확인한다.

```bash
for p in $(kubectl -n kubesphere-system get pods -o name | grep '^pod/ks-apiserver-'); do
  echo "===== $p ====="
  kubectl -n kubesphere-system logs "$p" --since=10m | \
    grep -Ei 'x509|certificate|unknown authority|xa\.dcr' || true
done
```

검증 기준: 이미지 경로 입력 단계에서 `x509: certificate signed by unknown authority`가 재발하지 않고 DEV `ks-apiserver`가 정상 상태를 유지해야 한다.

PRD 진입 조건: 위 검증 기준을 모두 충족한 경우에만 Task 1-3을 수행한다.

중단 조건: x509가 지속되거나 다른 TLS 오류로 변경되면 PRD에 동일 변경을 적용하지 않는다. DEV는 작업 전 상태와 비교해 복구 여부를 판정한다.

### Task 1-3. PRD Member에 동일 CA bundle 적용

DEV의 Add Container 검증이 성공한 뒤에만 PRD Member Bastion에서 수행한다. DEV에서 검증한 것과 동일한 Issuing/Root 인증서를 사용해 동일 bundle을 만든다.

먼저 PRD context와 현재 상태를 확인하고 백업한다.

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl -n kubesphere-system rollout status deployment ks-apiserver

mkdir -p "$HOME/ks-apiserver-secds-t2-backup"
kubectl -n kubesphere-system get deployment ks-apiserver -o yaml \
  > "$HOME/ks-apiserver-secds-t2-backup/ks-apiserver.before.yaml"

POD=$(kubectl -n kubesphere-system get pods -o name | \
  awk -F/ '/pod\/ks-apiserver-/{print $2; exit}')

CERT_DIR=$(kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  sh -c 'if [ -n "$SSL_CERT_DIR" ]; then printf "%s\n" "$SSL_CERT_DIR" | cut -d: -f1; else printf "/etc/ssl/certs\n"; fi')

echo "$CERT_DIR"

kubectl -n kubesphere-system exec "$POD" -c ks-apiserver -- \
  sh -c "test -d '$CERT_DIR' && ls -ld '$CERT_DIR'"
```

DEV와 동일한 bundle 파일을 준비하고 검증한다.

```bash
ISSUING=/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2IssuingCA.crt
ROOT=/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2ROOTCA.crt
CA_BUNDLE=/tmp/SECDS-T2-CA-BUNDLE.crt

cat "$ISSUING" "$ROOT" > "$CA_BUNDLE"
grep -c 'BEGIN CERTIFICATE' "$CA_BUNDLE"
openssl verify -CAfile "$ROOT" "$ISSUING"
```

ConfigMap과 Deployment patch를 DEV와 동일하게 적용한다.

```bash
kubectl -n kubesphere-system create configmap secds-t2-ca \
  --from-file=ca.crt="$CA_BUNDLE" \
  --dry-run=client -o yaml | \
  kubectl apply -f -

cat > /tmp/ks-apiserver-secds-t2-ca-patch.yaml <<EOF
spec:
  template:
    spec:
      volumes:
        - name: secds-t2-ca
          configMap:
            name: secds-t2-ca
            items:
              - key: ca.crt
                path: SECDS-T2-CA-BUNDLE.crt
      containers:
        - name: ks-apiserver
          volumeMounts:
            - name: secds-t2-ca
              mountPath: ${CERT_DIR}/SECDS-T2-CA-BUNDLE.crt
              subPath: SECDS-T2-CA-BUNDLE.crt
              readOnly: true
EOF

kubectl -n kubesphere-system patch deployment ks-apiserver \
  --type=strategic \
  --patch-file /tmp/ks-apiserver-secds-t2-ca-patch.yaml

kubectl -n kubesphere-system rollout status deployment ks-apiserver \
  --timeout=180s
```

검증 기준: PRD `ks-apiserver` rollout 완료 후 `CERT_DIR/SECDS-T2-CA-BUNDLE.crt`가 존재하고 인증서 개수가 `2`이며, PRD KubeSphere Add Container 이미지 입력에서 `unknown authority`가 발생하지 않아야 한다.

중단 조건: PRD `ks-apiserver`가 정상화되지 않으면 PRD 변경만 복구하고 DEV의 검증 완료 상태는 유지한다. 전체 작업 상태는 완료가 아닌 부분 완료/조치 필요로 기록한다.

## 2. 사후 작업

### Task 2-1. DEV·PRD 최종 검증

1. DEV와 PRD 각각에서 `ks-apiserver` rollout 상태를 확인한다.
2. DEV와 PRD 각각의 KubeSphere Project에서 **Creating a Deployment → Add Container**의 Harbor 이미지 경로 입력을 재검증한다.
3. 두 Member 모두 `ks-apiserver` 로그에 신규 `x509: certificate signed by unknown authority`가 발생하지 않는지 확인한다.
4. 작업 전·후 `secds-rootca`와 `ks-apiserver` 마운트 상태를 기록한다.
5. Host Cluster와 Harbor/LB 설정이 이번 작업에서 변경되지 않았음을 확인한다.

검증 기준: DEV와 PRD 모두 KubeSphere Add Container 이미지 입력 단계에서 Harbor x509 오류가 발생하지 않고 `ks-apiserver`가 정상 상태여야 한다.

Deployment 생성 후 Pod 단계에서 별도 `ImagePullBackOff`와 x509가 발생하면 이번 `ks-apiserver → Harbor` 조치와 분리한다. 해당 증상은 Worker Node/container runtime의 Harbor trust 경로 문제로 별도 이슈로 기록하고 이번 작업 범위를 확장하지 않는다.

### 통합 검증 기록

| Task | 확인항목 | 예상값 | 실제값 | 작업자 | 검증자 |
| --- | --- | --- | --- | --- | --- |
| 0-1 | T2 CA 식별 | `SECDS-T2IssuingCA`, `SECDS-T2ROOTCA` 확인 | 미기재 | 원문 미기재 | 원문 미기재 |
| 1-1 | DEV `ks-apiserver` rollout | rollout 완료, Pod 정상 | 미기재 | 원문 미기재 | 원문 미기재 |
| 1-2 | DEV Add Container Harbor 이미지 입력 | `unknown authority` 미발생 | 미기재 | 원문 미기재 | 원문 미기재 |
| 1-3 | PRD `ks-apiserver` rollout | rollout 완료, Pod 정상 | 미기재 | 원문 미기재 | 원문 미기재 |
| 2-1 | PRD Add Container Harbor 이미지 입력 | `unknown authority` 미발생 | 미기재 | 원문 미기재 | 원문 미기재 |

## [ 복구 방안 ]

### R-1. 복구 조건

- CA bundle 적용 후 대상 Member의 `ks-apiserver` rollout이 완료되지 않는다.
- 대상 Member의 KubeSphere 기능이 작업 전 상태로 정상화되지 않는다.
- `x509: certificate signed by unknown authority`가 지속되며 이번 변경의 효과가 확인되지 않는다.
- 적용 과정에서 기존 `ks-apiserver` 설정과 충돌하는 예상하지 못한 문제가 발생한다.

### R-2. 복구 절차

이번 작업은 기존 CA 설정을 수정하지 않고 신규 `secds-t2-ca` ConfigMap과 `ks-apiserver` Pod template 마운트만 추가하므로, 대상 Member에서 작업 직후 다른 Deployment 변경이 없다는 조건으로 직전 ReplicaSet으로 되돌린 뒤 신규 ConfigMap을 삭제한다.

```bash
kubectl -n kubesphere-system rollout history deployment ks-apiserver

kubectl -n kubesphere-system rollout undo deployment ks-apiserver

kubectl -n kubesphere-system rollout status deployment ks-apiserver \
  --timeout=180s

kubectl -n kubesphere-system delete configmap secds-t2-ca \
  --ignore-not-found
```

복구 후 마운트가 제거됐는지 확인한다.

```bash
kubectl -n kubesphere-system get deployment ks-apiserver -o yaml | \
  grep -n 'secds-t2-ca' || true
```

아무 출력이 없고 `ks-apiserver`가 정상 상태여야 한다. 작업 이후 다른 Pod template 변경이 이미 수행된 경우에는 `rollout undo`를 바로 실행하지 않고 작업 전 저장한 `ks-apiserver.before.yaml`과 현재 Deployment를 대조해 이번 `secds-t2-ca` 변경만 제거한다.

마지막으로 KubeSphere의 대상 Member 접근과 작업 전 기능 상태를 확인한다.

PRD 작업 실패 시 PRD만 복구하고, 이미 성공 검증된 DEV 변경은 PRD 실패만을 이유로 자동 복구하지 않는다. 전체 작업 결과에는 PRD 실패와 DEV 유지 상태를 명확히 기록한다.

## 작업 종료 확인

- [ ] 승인된 `SECDS-T2IssuingCA`와 `SECDS-T2ROOTCA`를 확인했다.
- [ ] DEV/PRD의 작업 전 `ks-apiserver` 상태와 기존 CA 관련 마운트를 저장했다.
- [ ] DEV Member에 T2 CA bundle 적용 후 `ks-apiserver` rollout을 완료했다.
- [ ] DEV Add Container 이미지 입력에서 `unknown authority`가 재발하지 않음을 확인했다.
- [ ] DEV 성공 후 PRD Member에 동일 T2 CA bundle을 적용했다.
- [ ] PRD Add Container 이미지 입력에서 `unknown authority`가 재발하지 않음을 확인했다.
- [ ] DEV·PRD `ks-apiserver`의 최종 정상 상태를 확인했다.
- [ ] Host Cluster와 Harbor/LB를 이번 작업에서 변경하지 않았음을 확인했다.
- [ ] 작업자와 검증자가 실행 결과를 기록·확인했다.

### 원문 불일치 및 확인 필요

현재 `KubeSphere SECDS-ROOT.crt ConfigMap Mount` 가이드는 `SECDS-ROOT.crt` 단일 CA를 `ca.crt`에 넣는 형태로 작성되어 있다. 그러나 사용자 제공 Xi'an Harbor TLS 출력에서는 서버가 `SECDS-T2IssuingCA`가 서명한 서버 인증서만 직접 제공하고, Bastion 검증 경로는 `SECDS-T2IssuingCA → SECDS-T2ROOTCA`로 확인됐다. 이번 작업에서는 이 실제 증적을 기준으로 `ca.crt`에 Issuing CA와 Root CA를 함께 포함한다. 기존 운영 가이드 자체의 개정은 이번 작업 범위에 포함하지 않는다.

이번 작업에서 사용할 승인된 T2 CA 파일은 `/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2IssuingCA.crt`와 `/app/dspaas/SCS_DKS_Kubernetes_Stack-v1.0/SECDS-T2ROOTCA.crt`로 확정한다. 실행 직전 `openssl x509 -noout -subject -issuer`로 Subject/CN만 재확인하고 그대로 사용한다.

작업 일정, 작업자, 검증자는 현재 자료에 기재되지 않았다.

### 보안 주의

인증서 본문은 ConfigMap 적용에 사용하되 작업계획서·실행 로그·스크린샷에는 전체 PEM 본문을 기록하지 않는다. Private Key는 본 작업에 사용하지 않으며 문서나 ConfigMap에 포함하지 않는다.
