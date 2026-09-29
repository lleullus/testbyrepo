# 개요

VCF Automation(VCFA) 환경의 Getting Started 가이드. VCF CLI 설치/설정, vcfa-authenticator 도우미 도구, Context 등록, 클러스터/영역 조회 명령어, Bastion 및 VPC 내 노드 SSH 접속 방법을 정리함.

## 핵심 내용

### Context 종류 및 인증 방식

* Context 타입: `k8s`, `cci`
* CCI = 다수 Supervisor Cluster들의 통합 인터페이스
* 인증방식:

  * `basic (username/password)` — local 계정, 환경변수 `VCF_CLI_VSPHERE_PASSWORD` 사용
  * `basic (api-token)` — VCFA 웹콘솔 (우측상단 계정 아이콘 → My Account → API Tokens)에서 생성
  * `oidc` — pinniped-auth 사용 (SSO 후 브라우저 오픈해 코드 획득)

### Context 권한 체계

| Tenancy            | Context                  | 주요 권한                                                                                                                                                                                                                                           |
| ------------------ | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Organization Admin | CCI                      | Organization(WLD) 범위 Computing, VPC, Storage 등 인프라 라이프사이클 관리. VPC/Limit/ipblock/loadbalancer 관리, Supervisor NamespaceClass/Region/Zone. `*.cci.vmware.com` (VCFA 메인 "Manage & Govern" 메뉴)                                                       |
| Organization User  | Supervisor               | VKS 클러스터 전체 라이프사이클 관리. Supervisor Namespace 별 권한 할당. CAPI CRDs (Cluster, VSphereCluster, KubeadmcontrolPlane, MachineDeployment, MachineSet, Machine 등), VirtualMachine/VirtualMachineService/VSphereMachine. `vmware.com && !*.cci.vmware.com` |
| Cluster Admin      | Supervisor Namespace CCI | 할당된 Supervisor Namespace 범위 내 클러스터 라이프사이클 관리. CAPI CRDs. DKS-C에서는 사용자에게 제공하지 않음                                                                                                                                                                 |
| Cluster User       | VKS (Cluster)            | 프로비저닝된 클러스터의 운영자 권한                                                                                                                                                                                                                             |

### VCF CLI 설치 (버전 9.0.2)

```
$ wget https://repository.samsungds.net/repository/proxy-yum-broadcom.jfrog.io-artifactory-vcfcli-rpm/packages/vcf-cli-9.0.2-1.x86_64.rpm
$ sudo rpm -ivh vcf-cli-9.0.2-1.x86_64.rpm
$ vcf version
```

* 다운로드 원천: `https://broadcom.jfrog.io/artifactory/vcf-distro`, `https://broadcom.jfrog.io/artifactory/vcfcli-rpm/`
* 실행파일만 필요시: `vcf-cli/linux/amd64/v9.0.2/vcf-cli.tar.gz`

### Harbor 인증서 설치

```
$ mkdir certs
$ cat << EOF | sudo tee certs/kh-prd-ia-mgd-harbor.samsungds.net.crt
-----BEGIN CERTIFICATE-----
(인증서 내용 — 원문 참조)
-----END CERTIFICATE-----
EOF
```

### Shell 환경 변수 설정 (~/.bashrc)

```bash
source <(kubectl completion bash)
alias k=kubectl
complete -o default -F __start_kubectl k
export VCF_CLI_VSPHERE_PASSWORD="Dks123!Dks123!!"
export VCF_CLI_VCFA_API_TOKEN="................"
$ source ~/.bash_profile
```

### Context 등록 — CCI

* 개발 WLD:

```
$ vcf context create dev-cci \
 --endpoint kh-prd-vcf-vcfa.samsungds.net \
 --type cci \
 --tenant-name dks-dev-org \
 --api-token woNFdUHNyMm5Zh4RYw0g8K5eCDqI1TtH \
 --insecure-skip-tls-verify
```

* 운영 WLD:

```
$ vcf context create cci \
 --endpoint kh-prd-vcf-vcfa.samsungds.net \
 --type cci \
 --tenant-name dks-org \
 --api-token hCGFnm8uEUIbqgC0ByWN0WCIS2H5dcIp \
 --insecure-skip-tls-verify
```

* 개발계 tdev:

```
$ vcf context create tdev-cci \
 --endpoint kh-dev-mgd-vra.samsungds.net \
 --type cci \
 --tenant-name KH-DEV-WDA-VKS \
 --api-token 8xCrNYVG0URI7OGhAGZaumWQghX11dTu \
 --insecure-skip-tls-verify
```

* Context 전환: `$ k config use-context cci`

### Context 등록 — Supervisor (k8s, basic auth)

* 개발 WLD: endpoint `12.201.34.5`, username `dks-sup-admin@vsphere.local`
* 운영 WLD: endpoint `12.201.17.5`, username `dks-sup-admin@vsphere.local`
* 기본 비밀번호 환경변수에 설정 필요

### VCF-CLI Manual

* 공식 매뉴얼: https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-0/building-your-cloud-applications/getting-started-with-the-tools-for-building-applications/installing-and-using-vcf-cli-v9/command-reference2.html

### 주요 CLI 명령어

**클러스터 목록 (`vcf cluster list -A -o wide`)**

* 컬럼: NAME, NAMESPACE, STATUS(running), CONTROLPLANE(3/3 or 1/1), WORKERS(3~10/10), KUBERNETES(v1.33.3+vmware.1-fips), KUBERNETESRELEASE(v1.33.3---vmware.1-fips-vkr.1)
* 대표 클러스터: bia-dev, cae-pcloud-prod, canvas, dbrgdev01, dks-magician-ax, prd-dksc-ic01-khm(~prd-dkso-ic01-khm) 등
* Worker 수: 대부분 3~5개, prd-dkso-ic01-khm는 10개

**프로젝트별 클러스터 (`v get cluster`)**

* 컬럼: PROJECT, NAME, CLUSTER, PHASE(Created), CLASS(small/medium/large/dev-*), VPC, AGE, CPU/MEMORY/STORAGE 사용량
* 프로젝트: bcm-test-project, dkssol-dev-project, dkssol-project, dkssol-qa-project, dkssol-prd-project 등

**VPC 목록 (`v get vpc`)**

* 컬럼: NAME, STATUS(✅), CIDRS, SNAT(12.201.18.x), NAMESPACES, QUOTA(5), CONSUMED(3), ALLOCATED(3), AVAILABLE(2), AGE
* CIDR 예: 172.1.0.0/24, 172.2.0.0/24 등

**Supervisor Namespace (`v get svns`)**

* 컬럼: PROJECT, NAME, CLUSTER, PHASE(Created), REGION(kh-prd-ia-wld01-region01), CLASS, VPC
* Region: 전체 kh-prd-ia-wld01-region01

**Region Quota (`v get quota`)** — Region: kh-prd-ia-wld01-region01

* Zone 3개: az01, az02, az03
* CPU: 1 Zone 4,838 GHz / 총 14,515 GHz, 사용 6,042 GHz (42%)
* Memory: 1 Zone 17,786 GiB / 총 53,360 GiB, 사용 16,923 GiB (32%)
* Storage: vks-pf-storage-policy, 총 60 TiB

### VCFA 컴포넌트 상태 체크 (`v healthy vcfa`)

* 체크 서비스: platform-statefulsets-core, platform-api-server-core, platform-control-plane-core, platform-daemonsets-core, platform-networking-daemonsets-core, vksm-services-prelude-deployments-core, platform-snapshots-snapshot, platform-storage-capacity-prom, platform-vmsp-platform-sftp, platform-node-disk-utilization-prom, platform-opsmgmt-dns, vksm-services-prelude-pods-core, platform-etcd-core, platform-machines-core, platform-vc-serviceaccount-http 등
* 전체 상태: ✅ OK (타입: core, http, prom, sftp, dns)

## 세부 정보

### vcfa-authenticator 설치 및 사용

* 설치 디렉토리: `$HOME/vcfa-authenticator`
* 다운로드:

```
$ wget --no-check-certificate https://github.samsungds.net/raw/dsec25527-id/shared/refs/heads/main/vcfa-authenticator/latest/vcfa-authenticator-linux-amd64
$ wget --no-check-certificate https://github.samsungds.net/raw/dsec25527-id/shared/refs/heads/main/vcfa-authenticator/latest/vcfa-authenticator.yaml
$ chmod +x vcfa-authenticator-linux-amd64
$ alias v=$HOME/vcfa-authenticator/vcfa-authenticator
```

* **필수 조건**: 실행 파일과 설정 파일(yaml)이 동일한 디렉토리에 존재해야 함
* Windows: kubectl.exe + vcfa-authenticator.exe 다운로드 후 PowerShell Profile 수정

**명령어**

* Context 전환: `v config use-context prod | dev | tdev`
* 현재 Context 확인: `v config current-context`
* kubeconfig 전체 가져오기:

```
$ v config use-context tdev
$ v kubeconfig generate > /tmp/kubeconfig
$ export KUBECONFIG=/tmp/kubeconfig
$ kubectl config get-contexts
$ kubectl config use-context cci
```

### SSH 접근

**Bastion**

* HIWare: 10.166.202.91, 계정: dspaas, 비밀번호: 삼성123!!
* `kh-prd-ai-wld01` — 운영계 운영 WLD Bastion
* `kh-prd-ai-wld02` — 운영계 개발 WLD Bastion
* `kh-dev-wda` — VCF 9.1 검증계 Bastion

**Bastion → VPC 노드 (Supervisor) 접속 정보**

* kh-prd-ai-wld01 (운영 WLD): dks-user@12.201.42.47 / Dks123!Dks123!!
* kh-prd-ai-wld02 (운영 개발 WLD): dks-user@12.201.42.48 / Dks123!Dks123!!
* kh-dev-wda (개발 VCF9.1검증): dks-user@10.169.61.25 / Dks123!Dks123!!

### VPC 내 노드 SSH — vPod 스크립트

```
$ ssh-install <cluster_name> # vPod 설치
$ ssh-exec <machine_name> # Machine SSH 접속
$ ssh-exec <machine_name> <cmd> # Machine SSH 명령어 실행
$ ssh-uninstall <cluster_name> # vPod 삭제
```

* 로그 조회: `ssh-exec <machine> cat /var/log/cloud-init-output.log`

### VPC 내 노드 SSH — kubectl Pod 기반

**Pod 생성 방식**

* 컨테이너 이미지: `kh-dev-wda-harbor.samsungds.net/docker.io/library/httpbin:latest`
* ssh-key Secret에서 `id_rsa` 마운트 (모드 0400)
* SSH 접속: `kubectl exec -it httpbin -n <ns> --context=supervisor -- ssh vmware-system-user@<node-ip>`

**1회성 run 방식**

* `kubectl -n <ns> --context=supervisor run vm-ssh -it --rm --image=... --restart=Never --overrides='<json>'`
* 변수: namespace_name, cluster_name, cmd(ssh 명령어)
* SSH 키 Secret: `<cluster_name>-ssh`에서 `ssh-privatekey` → `id_rsa` (모드 256)
* 메모리 요청: 2Gi

### 원본 참고

* vPod를 통한 노드 접근 방법: https://confluence.samsungds.net/spaces/dksSolution/pages/3788885727/
