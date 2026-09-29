# 개요
VCFA(Cloud Consumption Interface) CRDs 문서로, DKS 플랫폼의 CCI와 Supervisor 레이어에서 사용하는 Custom Resource Definitions의 구조, Naming Convention, Quota 관리, 그리고 클러스터 프로비저닝 프로세스에 대한 종합 가이드이다.

## 핵심 내용
### CCI CRDs 구조 및 관계
주요 관계:
- Supervisor Namespace : NamespaceClass = **1 : 1**
- VPC : Limit = **1 : 1**
- VPC : Supervisor Namespace = **1 : 1**
- Supervisor Namespace : VKS = **1 : 1**

#### CCI 주요 CRDs
| Scope | API Group | Kind | 설명 |
|---|---|---|---|
| Project | project.cci.vmware.com | Project | Tenant 단위 (Supervisor Namespace 그룹), DKS Platform에서는 재활용 |
| Authorization | authorization.cci.vmware.com | ProjectRole | 사전정의 - admin, edit_adv, edit, view |
| Authorization | authorization.cci.vmware.com | ProjectRoleBinding | User/Group 과 ProjectRole 바인딩. Namespaced 객체 |
| VPC | vpc.nsx.vmware.com | TransitGateway | 사전정의 |
| VPC | vpc.nsx.vmware.com | IPBlock | 3종류 - Private/Private TGW/External |
| VPC | vpc.nsx.vmware.com | VPCConnectivityProfile | VPC Topology 프로필 |
| VPC | vpc.nsx.vmware.com | Limit | IP 할당 정책, 대상 IPBlock (external) 과 할당 방식 정의 |
| VPC | vpc.nsx.vmware.com | VPC | SupervisorNamespace:VPC:Cluster = 1:1:1 |
| VPC | vpc.nsx.vmware.com | VPCAttachment | VPCConnectivityProfile 과 VPC 연결 |

#### IPBlock 3종류
- **Private**: VPC 생성 시 자동 생성, spec.visibility=Private, spec.systemOwned=true
- **Private TGW**: Multiple-VPC 간 통신을 위한 subnet, spec.visibility=Private, spec.systemOwned=false
- **External**: VPC 외부 subnet, spec.visibility=External, 이름이 콜론(:)으로 시작 (read-only)
- IPBlock(Public-TGW), IPBlock(External) 은 사전 정의, IPBlock(Private) 은 자동 생성

#### Limit 할당 방식 2종:
- 할당 가능 개수를 지정하는 방식
- CIDR를 지정하는 방식
VPC별로 Quota 변경(수동)을 감안하여 VPC별로 생성.

#### Supervisor Namespace 관련
| CRD | 설명 |
|---|---|
| SupervisorNamespaceClass | Supervisor Namespace 추상화 객체 |
| SupervisorNamespaceClassConfig | CPU, Memory, Storage quota 사전 정의. default quota 및 vm class 정의 |
| SupervisorNamespace | Quota 지정 가능한 최소 Tenant 단위 오브젝트 |

Supervisor NamespaceClassConfig Quota 규칙:
- Storage quota는 Supervisor Namespace에서 **override 할 수 없음**
- CPU, Memory quota는 zone과는 무관하게 지정

SupervisorNamespace 규칙:
- 수정 불가 (create/destroy만 가능, update/patch 불가)
- Storage는 limit 값 override 불가

### Quota CRDs
| Resources | CRD | Scope | Quota | 설명 |
|---|---|---|---|---|
| CPU/Memory/Storage | Supervisor Namespace | Region | O | Quota 지정 기본 단위. Storage: Storage Policy별, CPU/메모리: Zone별 지정. SupervisorNamespaceClassConfig에서 사전 정의, override 가능 (Storage 제외) |
| | SupervisorNamespaceClassConfig | Supervisor Namespace | O | CPU, Memory, Storage quota 사전 정의 |
| CPU/메모리 | Zone (topology.cci.vmware.com) | Region | O | Zone별 CPU, 메모리 quota 및 사용량 집계. supervisor context Zone 객체(topology.tanzu.vmware.com)와 다름에 주의 |
| | VirtualMachineClass | Supervisor Namespace | | CPU Core, Memory Spec 사전정의. CPU/메모리는 Supervisor Namespace 단위로 집계하지 않고 Zone(vCenter vSphere Cluster 범위)까지만 집계 |
| Storage | RegionStorageClassQuota | Region | | Region의 StorageClass별 quota 및 사용량 집계 |
| | StorageQuota | Supervisor Namespace | | Supervisor Namespace의 Storage Policy별 quota 및 사용량 조회. Supervisor Namespace별 1:1 생성 |
| | StoragePolicyQuota | Supervisor Namespace | | Supervisor Namespace에서 사용하는 Storage Policy별 사용량 집계 |
| | StoragePolicyUsage | Supervisor Namespace | | Supervisor Namespace에서 사용하는 Storage Policy별 vm, snapshot, pvc 3종 사용량 집계 |
| External-IP | IPBlock | Region | | CIDR 정의. 콜론 시작 IPBlock은 External-IP(사전정의), Private IPBlock은 자동 생성 |
| | IPBlockUsage | Region | | IPBlock의 allocated & available IP 목록. IPBlock별 1:1 생성 (CCI 목록 조회 권한 없음) |
| | Limit | Region | | IPBlock에 대한 quota 정의 (CIDR 또는 IP 개수). VPC의 spec.limitNames 속성에 할당 |
| | LimitState | Region | | Limit의 consumed IP 사용량 집계. Limit별 1:1 생성 |
| | VPCLimitState | VPC | | VPC에 할당된 Limit 객체들 consumed IP 사용량 집계. VPC별 1:1 생성. allocated IP (VPCIPAddressUsage)와 mismatch 발생 - consumed IP 집계 오류 추정 |
| | VPCIPAddressUsage | VPC | | VPC의 allocated & available IP 목록. VPC별 1:1 생성 (CCI 목록 조회 권한 없음) |

### Quota 변경 이슈 (제한사항)
- SupervisorNamespaceClass Quota 값을 상속받아 CPU, Memory, Storage Quota 지정됨
- SupervisorNamespace는 수정 불가 오브젝트
- create/destroy만 가능, update/patch 안됨
- **VCFA는 Supervisor Namespace Quota 변경 기능 없음** (VCF 9.1에서 적용 예정)
- vSphere Automation API (vCenter API) 활용해서 변경 가능
- vCenter 권한 필요

### Quota 조회 방법
**External-IP 사용량 조회** (SupervisorNamespace → VPC → Limit → LimitState):
```
kubectl get svns ${SVNS} -n ${PROJECT} -o jsonpath="{.spec.vpcName}"
kubectl get vpc ${VPC} -o jsonpath="{.spec.limitNames[0]}"
kubectl get limitstate ${LIMIT} -o jsonpath="{.quota.usage}"
```

**CPU/메모리 조회**:
```
kubectl get zone --field-selector="spec.regionName=${REGION}"
kubectl get zone ${ZONE} -o jsonpath="{.spec.cpuLimit}"
kubectl get zone ${ZONE} -o jsonpath="{.status.cpuUsed}"
kubectl get zone ${ZONE} -o jsonpath="{.spec.memoryLimit}"
kubectl get zone ${ZONE} -o jsonpath="{.status.memoryUsed}"
```

**Storage 조회**:
```
kubectl get regionstorageclassquota --field-selector="spec.regionName=${REGION}"
kubectl get ${NAME} -o jsonpath="{.spec.storageCapacity}"
kubectl get ${NAME} -o jsonpath="{.status.storageConsumed}"
```

**SupervisorNamespace 내부 Quota 조회**:
```
kubectl get svns ${SVNS} -n ${PROJECT} -o jsonpath="{.status.storageClasses[0].name}"
kubectl get svns ${SVNS} -n ${PROJECT} -o jsonpath="{.status.storageClasses[0].limit}"
kubectl get svns ${SVNS} -n ${PROJECT} -o jsonpath="{.status.zones[0].cpuLimit}"
kubectl get svns ${SVNS} -n ${PROJECT} -o jsonpath="{.status.zones[0].memoryLimit}"
```

### DKS Storage Quota 참고
ControlPlane: **136** GiB/노드당
- OS: 36 GiB (20 GiB + swap 16 GiB)
- /var/lib/containerd: 50 GiB
- /var/log/kubernetes: 30 GiB
- /var/lib/etcd: 20 GiB

Worker: **116** GiB/노드당
- OS: 36 GiB (20 GiB + swap 16 GiB)
- /var/lib/containerd: 80 GiB

※ 3 Control-Plane, 2 Workers = **640** GiB (OS 영역 Swap 부분도 고려 필요)

### Naming Convention
| 항목 | 크기 | 코드 | 설명 |
|---|---|---|---|
| REGION_CODE | 2 | kh | KH |
| | | ta | TA |
| | | ca | CAE |
| ZONE_TYPE | 1 | s | Single |
| | | m | Multi |
| DOMAIN | 3 | prd | Production (운영 클러스터) |
| | | dev | Production (Development) (운영 클러스터/개발 서비스) |
| | | stg | Staging (스테이징 클러스터) |
| | | tst | Development (개발 클러스터) |
| VERSION | 4 | pa01 | Kubernetes v1.22.10 |
| | | pb01 | Kubernetes v1.26.13 |
| | | ic01 | VKS / Supervisor 버전 |

- Project: 운영 WLD=dkssol-project, 개발 WLD=dkssol-dev-project
- Cluster: (DOMAIN)-(APP NAME)-(VERSION)-(REGION_CODE)(ZONE_TYPE)
- VPC: 클러스터명과 동일 (VPCAttachment는 (VPC_NAME):default)
- NamespaceClass: 클러스터명과 동일
- Namespace: 클러스터명 + **랜덤 character (5자리, 지정 불가능)**

### CAPI CRDs (Cluster API)
※ Cluster Admin / Cluster User 권한
| Kind | 설명 |
|---|---|
| Machine | 모든 머신은 변경 불가능. 생성되면 레이블/주석/상태 제외 업데이트 불가, 삭제만 가능 |
| MachineDeployment | MachineSets를 조정해서 원하는 수의 machine이 실행되도록 함. Kubernetes Deployment와 유사 |
| MachineSet | 특정 Machine 템플릿에 따라 일정한 수의 Machine 유지. Kubernetes ReplicaSet과 유사. 직접 사용 X, MachineDeployment가 상태를 조정하는 데 사용 |
| MachineHealthCheck | MachineSet 또는 KubeadmControlPlane 소유 머신만 지원. 노드 복구: 해당 머신을 교체하는 방식으로 수행. MachineSet 소유 노드만 복구 |
| BootstrapData | cloud-init 등 머신 노드 초기화 데이터 |
| ClusterClass | CAPI Spec으로 유사한 클러스터를 여러 개 생성. VCF 9.0은 Built-in ClusterClass 기본 제공. DKS는 커스터마이즈하여 사용 |

### 클러스터 프로비저닝 프로세스 (11단계)
| 단계 | 주요 작업 | 인터페이스 | 상세 |
|---|---|---|---|
| 1 | Cluster RoleBinding 생성 | K8s CRD | YAML 생성하여 권한 부여 |
| 2 | ArgoCD로 클러스터 앱 배포 | REST API | 클러스터 앱 배포 요청 API 호출 |
| 3 | Carvel 애드온 배포 | REST API | Carvel 애드온 배포 |
| 4 | 클러스터 생성 health Check | REST API | 주기적 Polling으로 Application Health 상태 조회. 모든 machine이 health 상태여야 다음 단계 진행 |
| 5 | kubeconfig 시크릿 조회 | K8s CRD | Secret 리소스에서 kubeconfig 추출 |
| 6 | ArgoCD에 클러스터 등록 | REST API | 워크로드 클러스터 등록 |
| 7 | etcd 시크릿 조회 | K8s CRD | etcd 관련 Secret의 데이터 조회 |
| 8 | Helm 애드온 앱's 배포 | REST API | etcd 인증 정보 주입 후 대상(Target) 클러스터에 Helm Application 순차 배포 |
| 9 | VCFA networkInfos 조회 | K8s CRD | crd.nsx.vmware.com/v1alpha1 kind: networkInfos 조회하여 SNAT IP 추출 |
| 10 | 콘솔에 클러스터 정보 전달 | GraphQL API (Mutation) | UI로 최종 데이터 반환 |

### 클러스터 프로비저닝 완료 후 콘솔 프로세스 (4단계)
| 단계 | 주요 작업 | 인터페이스 | 상세 |
|---|---|---|---|
| 1 | 요청 데이터 검증 | GraphQL API (Mutation) | 클러스터 정보 데이터 검증 |
| 2 | 자원 생성/수정/삭제 | REST API + SQL | 생성/수정/삭제 작업 |
| 3 | 진행 상태 변경 | SQL | portal.order 테이블 상태 변경 |
| 4 | 결과 메일 발송 | REST API (Knox) | 처리 결과 메일 발송 |

**자원 생성/수정 단계**:
1. DB 사용자 클러스터 권한 추가 (SQL: portal.user_resource_role_ref)
2. APISIX Upstreams 생성/수정 (REST API)
3. APISIX Routes 생성/수정 (REST API)
4. 클러스터 Role 생성/수정 (REST API)
5. 클러스터 Role Binding 생성/수정 (REST API)
6. Harbor 레지스트리 생성 (REST API) - 최초 클러스터 생성 시

**자원 삭제 단계**:
1. DB 사용자 클러스터 권한 삭제 (SQL: portal.user_resource_role_ref)
2. APISIX Routes 삭제 (REST API)
3. APISIX Upstreams 삭제 (REST API)
4. 리소스 IP 할당 삭제 (SQL: portal.resource_ip - Pod IP, Service IP, VPC IP)
5. 즐겨찾기 삭제 (SQL: portal.user_bookmark)
6. Harbor 프로젝트 삭제 (REST API) - 마지막 클러스터 삭제 시

## 주의사항 / 예외 / 확인 필요
- **Quota 변경 불가**: VCFA는 Supervisor Namespace Quota 변경 기능 없음 (VCF 9.1 적용 예정). vCenter API로만 변경 가능.
- **Storage override 불가**: Storage quota는 SupervisorNamespaceClassConfig 값을 override 할 수 없음.
- **SupervisorNamespace 수정 불가**: create/destroy만 가능.
- **VPCLimitState mismatch**: allocated IP (VPCIPAddressUsage)와 consumed IP 집계 간 mismatch 발생 - 집계 오류 추정.
- **Zone 객체 혼동 주의**: CCI CRDs의 Zone (topology.cci.vmware.com) 은 supervisor context의 Zone 객체(topology.tanzu.vmware.com)와 다름.
- **IPBlockUsage/VPCIPAddressUsage**: CCI 목록 조회 권한 없음 (1:1 생성 필요).
- **Namespace 랜덤 5자리**: 생성 시 자동 할당되며 지정 불가능.