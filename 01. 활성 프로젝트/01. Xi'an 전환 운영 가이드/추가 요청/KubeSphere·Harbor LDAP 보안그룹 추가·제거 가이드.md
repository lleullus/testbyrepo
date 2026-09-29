---
title: "KubeSphere·Harbor LDAP 보안그룹 추가·제거 가이드"
created: 2026-08-29
status: draft
tags:
  - kubesphere
  - harbor
  - ldap
  - security-group
scope: "Xi'an 전환 운영 가이드"
---

# KubeSphere·Harbor LDAP 보안그룹 추가·제거 가이드

- 대상: Xi'an KubeSphere·Harbor 운영자
- 조건: KubeSphere와 Harbor가 동일 LDAP에 이미 연동된 상태에서 로그인 또는 Project 권한용 보안그룹을 추가·제거할 때 사용한다.
- 범위: LDAP 연동 구성은 변경하지 않고 KubeSphere userSearchFilter와 Harbor Project의 LDAP Group만 관리한다.

## 1. KubeSphere LDAP 로그인 허용 그룹 추가·제거

### 1.1 현재 ConfigMap 백업

```bash
kubectl get cm -n kubesphere-system kubesphere-config -o yaml > kubesphere-config-backup-$(date +%Y%m%d-%H%M%S).yaml
```

현재 Filter를 확인한다.

```bash
kubectl get cm -n kubesphere-system kubesphere-config -o yaml | grep userSearchFilter
```

### 1.2 기본 상태 — SG1599만 허용

```yaml
userSearchFilter: (&(objectclass=user)(memberOf=CN=SG1599,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net))
```

### 1.3 SG1600, SG1590, SG1591 추가

작업 전 각 Group DN이 실제 AD의 승인된 DN과 일치하는지 확인한다.

SG1599, SG1600, SG1590, SG1591 중 하나에 속하면 로그인할 수 있도록 memberOf 조건을 |(OR)로 묶는다.

```yaml
userSearchFilter: (&(objectclass=user)(|(memberOf=CN=SG1599,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1600,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1590,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1591,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)))
```

> (&(memberOf=A)(memberOf=B))처럼 그룹을 &로 연결하지 않는다. 이렇게 작성하면 A와 B에 모두 속한 사용자만 허용된다.

### 1.4 그룹 제거 예시 — SG1590 제거

변경 전:

```yaml
userSearchFilter: (&(objectclass=user)(|(memberOf=CN=SG1599,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1600,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1590,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1591,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)))
```

SG1590 조건만 제거한 후:

```yaml
userSearchFilter: (&(objectclass=user)(|(memberOf=CN=SG1599,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1600,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)(memberOf=CN=SG1591,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net)))
```

### 1.5 하나의 그룹만 남았을 때

SG1599만 남으면 | 블록을 제거하고 단일 조건으로 정리한다.

```yaml
userSearchFilter: (&(objectclass=user)(memberOf=CN=SG1599,OU="Security Groups",OU=Groups,OU=KOR,OU=Locations,DC=samsungds,DC=net))
```

### 1.6 ConfigMap 수정

```bash
kubectl edit cm -n kubesphere-system kubesphere-config
```

data.kubesphere.yaml의 기존 userSearchFilter만 변경하고 저장한다.

### 1.7 ks-apiserver 반영

```bash
kubectl rollout restart -n kubesphere-system deploy ks-apiserver
kubectl rollout status -n kubesphere-system deploy ks-apiserver
```

### 1.8 검증

추가 작업 후:

- SG1599에만 속한 LDAP 계정 로그인 성공
- SG1600에만 속한 LDAP 계정 로그인 성공
- SG1590에만 속한 LDAP 계정 로그인 성공
- SG1591에만 속한 LDAP 계정 로그인 성공
- 네 그룹 어디에도 속하지 않은 LDAP 계정 로그인 실패

제거 작업 후:

- 제거한 그룹에만 속한 LDAP 계정 로그인 실패
- 남아 있는 허용 그룹 계정 로그인 성공

## 2. Harbor LDAP Group 추가·제거

Harbor의 기존 LDAP 연동 설정은 변경하지 않는다.

### 2.1 LDAP Group 추가

1. Harbor 관리자 계정으로 로그인한다.
2. **Projects**에서 대상 Project를 선택한다.
3. **Members**로 이동한다.
4. **+Group**을 클릭한다.
5. 추가할 LDAP Group을 입력 또는 검색한다.
6. 승인된 Harbor Role을 선택한다.
7. 추가한다.

검증:

- 추가한 LDAP Group의 사용자로 Harbor에 로그인한다.
- 대상 Project가 보이는지 확인한다.
- 부여한 Role에 맞는 Pull·Push 또는 관리 권한을 확인한다.

### 2.2 LDAP Group 제거

1. **Projects**에서 대상 Project를 선택한다.
2. **Members**로 이동한다.
3. 제거할 LDAP Group을 선택한다.
4. **Remove**를 실행한다.

검증:

- 제거한 LDAP Group에만 의존하던 사용자로 대상 Project 권한이 회수됐는지 확인한다.
- 다른 사용자 또는 다른 Group을 통해 별도 권한을 가진 계정은 해당 권한이 유지될 수 있으므로 별도로 확인한다.

## 3. 완료 확인

| 대상 | 확인 항목 |
|---|---|
| KubeSphere | 변경 전 kubesphere-config 백업 완료 |
| KubeSphere | userSearchFilter에 승인된 Group만 포함 |
| KubeSphere | ks-apiserver rollout 완료 |
| KubeSphere | 추가 Group 로그인 성공 / 제거 Group 로그인 실패 확인 |
| Harbor | 대상 Project에 LDAP Group 추가 또는 제거 완료 |
| Harbor | 추가 Group 권한 동작 / 제거 Group 권한 회수 확인 |

## 근거

| 사실 주장 | 근거 파일·섹션/행 |
|---|---|
| KubeSphere는 kubesphere-config의 LDAPIdentityProvider와 userSearchFilter를 사용하고 변경 후 ks-apiserver를 재기동한다. | 30. 구축 및 전환/Host 클러스터/05.1.1.4 Re-deployment of Pods according to the DKS Standard.md L275–400 |
| 기존 KubeSphere 예시에 SG1599의 memberOf Filter가 기록돼 있다. | 같은 문서 L331–359 |
| Harbor는 Global AD 계정으로 로그인하며 AD 보안그룹 멤버십을 사용 조건으로 설명한다. | 50. 운영/07. DKS User Guide/02. Harbor User Guide.md L25–38, L55–63 |
| Harbor Project의 권한은 Members에서 관리한다. | 50. 운영/06. Harbor Manual/03. Managing Users.md L19–87 |
