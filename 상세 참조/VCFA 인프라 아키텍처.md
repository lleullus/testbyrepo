# 개요
VCFA(VMware Cloud Foundation Automation) 인프라 아키텍처의 주요 구조를 정리한 문서. Workload Domain, Region/Zone, Tenancy, VPC, Load Balancer 등 VCF 핵심 구성 요소와 상호관계를 설명함. DS Cloud Kubernetes Service(DKS) 기반 운영 환경의 참조 자료.

## 핵심 내용
### 1. VCF Fleet & Domain 구조
- **VCF Fleet : VCF Instance = 1 : N**
- **VCF Fleet : VCF Automation : VCF Operation : VCF Instance = 1 : 1 : 1 : N**
- **VCF Instance : Management Domain : Workload Domain = 1 : 1 : N**
- **Workload Domain** : 하나 이상의 vSphere 클러스터로 구성된 논리적 가상화 자원 단위. VCFA로 생성/관리.
- **Management Domain** : SDDC Manager(VCF Operation)가 Central Workload Domain 및 Remote Workload Domain, 개별 Remote Cluster를 관리.
- Workload Domain은 1개 이상의 vSphere Cluster로 구성.

### 2. Region & Zone 구조
- **Workload Domain : Region : Zone = 1 : 1 : N**
- **Organization : Supervisor = 1 : N** (운영계/개발계는 1:1 구성)
- **Supervisor** : Compute, VPC, Storage 등 클라우드 인프라를 CRD(Custom Resource Definition)로 관리하는 Kubernetes Cluster. VCFA의 기본 인프라 관리 단위.
- Stretched Cluster : Computing 자원을 물리적으로 떨어진 두 데이터센터(AZ) 간에 동기식으로 복제/확장하는 HA 구성.

### 3. VCFA Tenancy
- **Organization** : 클라우드 인프라에 대한 논리적 Tenant 단위 (격리)
- **vNamespace (vSphere Namespace)**
  - Supervisor 클러스터 내에서 Tenant별 리소스를 논리적으로 분할/관리하는 Tenancy 단위
  - Resource(CPU, Memory, Storage) Quota 정의
  - VKSA 관점에서 DKS 네임스페이스 서비스와 유사한 목적
- VCFA Tenant 역할 구분:
  - **Provider Admin** : Workload Domain, Supervisor 관리
  - **Organization Admin** : Project, vSphere Namespace 생성/관리
  - **Organization User** : vSphere Namespace 기능 사용, VKS Cluster 사용자

### 4. VPC Model
- **Project : Transit G/W : VPC (VPC G/W) = 1 : 1 : N**
- **VPC : SNAT (external ip) = 1 : 1**
- VPC 내부 VM들은 동일한 SNAT IP(outbound/external-ip)로 NAT됨
- VCF는 동일 VPC 내 VM 간 통신 제한 없음 (**Security Group 개념 없음**)

### 5. Load Balancer Networking
- L/B는 vSphere Supervisor Control-Plane VM들과 **Management Network**로 연결.
- 어플리케이션 트래픽은 L/B VIP로 유입, 지정된 IP Pools로 포워딩되어 각 워크로드로 NAT됨.
- **Two-arm configuration** : L/B VIP와 IP Pools NIC을 분리 — incoming과 포워딩 트래픽이 별도 NIC 통과, 최초 요청 IP 유지.
- **Single-arm configuration** : L/B VIP와 IP Pools NIC을 동일 NIC 사용 시, incoming 트래픽과 포워딩 트래픽이 동일한 NIC 통과 → 최초 요청 IP를 읽어버리는 문제 발생.

## 세부 정보
| 항목 | 내용 |
|------|------|
| SDDC | Software Defined Data Center — 컴퓨팅, 스토리지, 네트워킹, 보안 통합 관리 |
| NSX | 네트워크 가상화 및 보안 플랫폼 |
| vSphere Cluster & Rack | 아키텍처 참조 이미지 존재 |
| VCF Region & Zone | 아키텍처 참조 이미지 존재 |
| VCFA Tenancy | 아키텍처 참조 이미지 존재 |
| VPC Model | VMware Cloud Foundation 공식 블로그 참조: VPC Centralized Network Connectivity – With Guided Edge Deployment |
| Load Balancer | VMware vcf-9-0 및 이후 버전 문서 참조 |
| 별첨 | Broadcom 박경진 차장 작성: VCF Integrated Layered Architecture and Component Interactions (DS Confluence) |

## 주의사항 / 예외 / 확인 필요
- VCF는 동일 VPC 내에서 Security Group 기능이 없음 (통신 제한 없이 VM 간 통신 가능).
- LB single-arm 구성 시 최초 요청 IP 손실 이슈 발생 — 운영 시 Two-arm 구성 권장.
- Management Domain은 SDDC Manager를 통해 중앙/원격 Workload Domain을 모두 관리 가능.
- Organization과 Supervisor의 관계는 일반적으로 1:N이나, 운영계/개발계 분리 환경에서는 1:1로 구성됨.