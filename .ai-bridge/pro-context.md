# 2026-09-01~03 강사용 대본 재작성 근거

Generated: 2026-08-30T03:45:32.391Z
Workspace: /mnt/d/개발방법론/개발방법론
Workspace ID: ws_bc1ab1f757f675c4b69ad43b
Write mode: workspace
Bash mode: full
Tool mode: standard

Purpose: paste this bundle into a high-context ChatGPT model when that model cannot call the CodexPro MCP tools directly.
Instruction for ChatGPT: use this as repository context, produce a narrow Codex execution plan, and avoid inventing files or runtime facts not shown here.

## Repository Tree

.
├── 01. 활성 프로젝트/
│   ├── 01. Xi'an 전환 운영 가이드/
│   └── 02. NetApp SVM 신규 SC + SVM 추가 테스트 (1차)/
├── 02. 활성 운영/
│   └── 01. 작업계획서/
├── 03. 지식/
│   ├── 01. Kubernetes 운영 런북/
│   ├── 02. 문제 구조화와 아키텍처적 사고/
│   └── 20. 개발 도구 운영/
├── 16. Linux 기반/
│   ├── _recovery/
│   ├── 02. 프로세스·CPU·PID/
│   ├── 03. 메모리·cgroup·OOM/
│   ├── 04. 디스크·파일시스템·입출력/
│   ├── 05. 커널·호스트 장애/
│   ├── 06. 격리·권한 경계/
│   └── 07. 호스트 네트워크/
├── 짬/
│   ├── 아카이브/
│   └── 템플릿/
├── # 원인을 찾기 전에, 가능한 구조부터 구분하라.md
├── AGENTS.md
├── LLM 문서 작성 및 검수 원칙 - Oracle 적대 검증 합의.md
├── Pasted image 20260815113918.png
├── Pasted image 20260815114223.png
├── Pasted image 20260815114228.png
├── Pasted image 20260815121843.png
├── 무제.canvas
├── 무제.md
└── 최종 4순위 라우팅 매트릭스.md

## Git Status

```text
fatal: not a git repository (or any parent up to mount point /mnt)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
```

## Recent Commits

```text
fatal: not a git repository (or any parent up to mount point /mnt)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
```

## Selected Files

Changed files detected: pping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
Auto-include important root files: no
Auto-include changed files: no
Explicit selected paths: 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-08-27/오후/02. Harbor 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오전/01. Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오후/01. Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오후/02. External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-02/오전/01. Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-02/오후/01. PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오전/01. Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오전/02. Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오후/01. 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오후/02. 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본.md
Extra globs: none
Files included below: 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-08-27/오후/02. Harbor 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오전/01. Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오후/01. Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오후/02. External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-02/오전/01. Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-02/오후/01. PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오전/01. Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오전/02. Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오후/01. 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오후/02. 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증.md, 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수.md

## File Contents

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-08-27/오후/02. Harbor 강사용 전체 대본.md

Bytes: 26216
SHA-256: 1db0cf36f889c7691a8314eb56c1b998716c7ef39948d32454d36b6e5df240e8
Lines: 1-427 of 427

```markdown
  1 | ---
  2 | title: "Harbor 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-08-27 Xi'an 현지 Harbor Manual 3.1~3.3 강의 대본"
  6 | created: "2026-08-26"
  7 | updated: "2026-08-26"
  8 | ---
  9 | 
 10 | # Harbor 강사용 전체 대본
 11 | 
 12 | > [!important] 사용 방법
 13 | > 이 대본은 **수강생이 Kubernetes와 Harbor를 거의 모른다는 전제**로 작성했다. 8/25 내용을 기억한다고 가정하지 않는다. 기술 용어부터 말하지 말고, 먼저 왜 필요한지와 역할을 쉬운 말로 설명한 뒤 실제 이름을 붙인다.
 14 | 
 15 | ## 0. 강사가 머릿속에 들고 갈 설명 공식
 16 | 
 17 | ```text
 18 | 문제부터 말한다
 19 | → 필요한 역할을 쉬운 말로 설명한다
 20 | → 그 역할의 기술 이름을 붙인다
 21 | → Xi'an 실제 값을 보여준다
 22 | → Manual 절차로 들어간다
 23 | → 완료 기준을 설명한다
 24 | → 장애 시 첫 단절 지점을 찾는다
 25 | ```
 26 | 
 27 | ## 0-1. 오늘 전체 한 줄
 28 | 
 29 | ```text
 30 | Application 실행 원본이 필요하다
 31 | → Image
 32 | → 여러 서버가 같이 쓰려면 중앙 저장소가 필요하다
 33 | → Registry
 34 | → Xi'an에서는 Harbor
 35 | → Project로 Image 영역을 나눈다
 36 | → User / Role을 연결한다
 37 | → Push / Pull
 38 | → 다음 교육에서 Kubernetes가 Private Image를 사용하는 방법으로 연결
 39 | ```
 40 | 
 41 | ---
 42 | 
 43 | # 1. 시작 — Harbor라는 단어부터 설명하지 않는다
 44 | 
 45 | > 오늘은 Harbor Manual을 보겠습니다.
 46 | >
 47 | > 그런데 Harbor 메뉴부터 바로 보지 않겠습니다. Harbor가 왜 필요한지 모르면 `Project`, `Repository`, `Push`, `Pull`이라는 단어를 외워도 실제 운영할 때 연결이 안 됩니다.
 48 | >
 49 | > 그래서 아주 앞에서부터 다시 시작하겠습니다. 어제 들었던 Kubernetes 내용을 기억하고 있다고 가정하지 않겠습니다.
 50 | 
 51 | ![[harbor-image-container-concept.png]]
 52 | 
 53 | *Application 실행 요소를 하나의 Container Image로 묶고, 그 Image를 실행하면 Pod 안의 Container가 되는 흐름*
 54 | 
 55 | ## 1.1 Image부터 다시 설명
 56 | 
 57 | > Application을 실행하려면 프로그램뿐 아니라 필요한 파일과 Library, 실행환경도 함께 있어야 합니다.
 58 | >
 59 | > **그래서**, 이 요소들을 하나로 묶어 동일한 형태로 전달할 수 있게 만든 실행 원본이 **Container Image**입니다.
 60 | >
 61 | > Image를 실제로 실행한 상태가 **Container**입니다. Kubernetes에서는 이 Container가 **Pod 안에서** 실행됩니다.
 62 | >
 63 | > **하지만**, Worker가 여러 대라면 같은 Image를 각 Worker에 어떻게 전달할지 정해야 합니다.
 64 | 
 65 | ## 1.2 왜 중앙 저장소가 필요한지 설명
 66 | 
 67 | > Kubernetes에서 Application Container가 실행되는 서버를 **Worker Node**라고 합니다. Worker가 한 대라면 Image를 직접 복사해 사용할 수도 있습니다.
 68 | >
 69 | > **하지만**, Worker가 여러 대면 같은 복사를 반복해야 합니다. 일부 Worker에는 이전 Version이 남을 수 있고, 새로 추가되거나 Application을 새로 배치한 Worker에는 필요한 Image가 없을 수 있습니다.
 70 | >
 71 | > **그래서**, Image를 한곳에 보관하고 모든 Worker가 그곳에서 필요한 Image를 가져오게 합니다. 이 **Container Image 중앙 저장소**를 **Registry**라고 합니다.
 72 | >
 73 | > Registry는 중앙 Image 저장소를 가리키는 일반적인 이름입니다. Xi'an에서는 이 역할을 담당하는 실제 제품이 필요합니다.
 74 | 
 75 | ## 1.3 이제 Harbor라는 이름을 붙인다
 76 | 
 77 | > Xi'an DKS에서는 **Harbor**가 Registry 역할을 담당하고 Image를 한곳에 보관합니다.
 78 | >
 79 | > **하지만**, 조직 내부 Image를 아무나 저장하거나 가져가게 할 수는 없습니다.
 80 | >
 81 | > **그래서**, Harbor는 사용자 인증과 접근 권한을 확인하는 **Private Registry**로 운영합니다.
 82 | >
 83 | > Harbor를 사용할 때는 Image가 저장소로 들어가는 방향과 저장소에서 나오는 방향을 구분해야 합니다.
 84 | 
 85 | ## 1.4 Push와 Pull을 쉬운 말로 설명
 86 | 
 87 | > Harbor에 Image를 올리는 동작을 **Push**, Harbor에서 Image를 가져오는 동작을 **Pull**이라고 합니다.
 88 | >
 89 | > Developer나 CI가 Image를 Harbor에 Push하고, Kubernetes Worker는 필요한 Image를 Pull해서 Container를 실행합니다.
 90 | >
 91 | > **하지만**, Push와 Pull이 동작하려면 Harbor 자체가 준비되어 있어야 하고, Image를 저장할 Project와 이를 사용할 User 권한도 필요합니다.
 92 | 
 93 | ---
 94 | 
 95 | # 2. 오늘 세 Manual의 관계를 먼저 정리한다
 96 | 
 97 | > 오늘 원본 Manual은 3.1 Harbor Installation, 3.2 Create a project, 3.3 Managing Users로 구성됩니다.
 98 | >
 99 | > 3.1은 Harbor 자체를 구축하는 플랫폼 기반이고, 3.2는 Application이나 Team이 사용할 Image 공간을 만들며, 3.3은 그 공간을 사용할 User와 권한을 연결합니다.
100 | >
101 | > **하지만**, 이 세 작업을 모든 요청마다 처음부터 반복하는 것은 아닙니다. 현재 Xi'an에는 Harbor가 이미 구축되어 있으므로 새로운 Project 요청이 들어와도 Harbor를 다시 설치하지 않습니다.
102 | >
103 | > **따라서**, 3.1에서는 Harbor가 어떤 기반에서 동작하고 무엇으로 정상 여부를 판단하는지 이해하고, 3.2와 3.3에서는 반복되는 Project와 User 운영을 다룹니다.
104 | 
105 | ---
106 | 
107 | # 3. 3.1 Harbor Installation — 네 가지 쉬운 질문부터 시작한다
108 | 
109 | > Harbor도 결국 하나의 서비스입니다. 정상적으로 사용하려면 실행할 환경, 사용자가 찾아오는 경로, HTTPS 신뢰, Image가 계속 남을 저장공간이 필요합니다.
110 | >
111 | > **그래서**, 설치 구조를 기술 이름부터 외우지 않고 `어디에서 실행하는가`, `어떻게 찾아오는가`, `HTTPS에서 어떻게 신뢰하는가`, `Image 데이터는 어디에 남는가`라는 네 가지 질문으로 나눕니다.
112 | >
113 | > Docker, FQDN, CA, `data_volume` 같은 실제 이름은 각 질문의 역할을 이해한 뒤 연결합니다.
114 | 
115 | ## 3.1 어디에서 실행하는가
116 | 
117 | > Harbor를 실행하려면 서버가 필요합니다. Xi'an Manual에서는 Harbor VM을 준비하고 그 위에서 Harbor를 실행합니다.
118 | >
119 | > **그래서**, VM의 OS 위에 Docker를 설치하고 여러 Harbor Container를 실행합니다. Docker는 Container 실행을 담당하고, `docker-compose`는 여러 Harbor Container를 함께 관리합니다.
120 | >
121 | > Docker와 `docker-compose`의 Version은 외울 값이 아니라 실제 설치 시 승인된 Manual과 현장 상태에서 확인할 값입니다.
122 | >
123 | > **하지만**, Harbor가 서버에서 실행된다는 사실만으로 사용자와 Worker가 Harbor를 찾아올 수 있는 것은 아닙니다.
124 | 
125 | ## 3.2 사용자는 어떻게 찾아오는가
126 | 
127 | > 사용자와 Worker가 Harbor 서버의 IP를 직접 외우는 대신 서비스 이름으로 접근합니다. 이런 전체 도메인 이름을 **FQDN**이라고 합니다.
128 | >
129 | > 원본 Manual에는 Xi'an Harbor FQDN이 `xa.dcr.dks.samsungds.net`으로 기록돼 있습니다. 실제 운영에서는 현재 승인된 주소를 다시 확인합니다.
130 | >
131 | > **그래서**, 사용자와 Worker의 요청은 FQDN을 기준으로 DNS, Network와 Firewall, HTTPS Port를 거쳐 Harbor에 도달합니다.
132 | >
133 | > **하지만**, 내 PC에서 Harbor 화면이 열린다고 모든 Worker의 접근까지 정상인 것은 아닙니다. 각 Client가 사용하는 DNS와 Network 경로를 따로 확인해야 합니다.
134 | >
135 | > 통신 경로가 열려 있어도 Client가 접속한 Harbor를 신뢰하지 못하면 HTTPS 연결은 실패할 수 있습니다.
136 | 
137 | ## 3.3 HTTPS에서 어떻게 신뢰하는가
138 | 
139 | > Harbor는 HTTPS로 접속합니다. 통신 경로가 열리면 Client는 자신이 접속한 서버가 요청한 FQDN의 Harbor가 맞는지 확인합니다.
140 | >
141 | > 이 신뢰를 확인하려면 Server Certificate, Private Key, Root와 Intermediate CA의 역할을 구분해야 합니다.
142 | 
143 | ### Server Certificate
144 | 
145 | > Harbor가 자신이 해당 FQDN의 서버임을 Client에 보여주는 인증서입니다.
146 | 
147 | ### Private Key
148 | 
149 | > Server Certificate와 한 쌍으로 사용되는 서버의 비밀키입니다. 화면이나 문서에 절대 노출하지 않습니다.
150 | 
151 | ### Root / Intermediate CA
152 | 
153 | > Client가 Server Certificate를 발급한 체인을 신뢰할 수 있는지 판단하는 기준입니다.
154 | 
155 | > Server Certificate, Private Key, CA는 서로 바꿔 쓸 수 없는 별도 요소입니다.
156 | >
157 | > **하지만**, 인증서 Chain이 완전하지 않거나 Client가 해당 CA를 신뢰하지 않으면 `x509: certificate signed by unknown authority`가 발생할 수 있습니다. 이 경우 비밀번호부터 바꾸는 것은 원인에 맞지 않습니다.
158 | >
159 | > **그래서**, 접속한 FQDN, Server Certificate, 인증서 Chain, Client의 CA 신뢰를 순서대로 확인합니다.
160 | >
161 | > HTTPS 신뢰가 해결돼도 Harbor Container가 재시작된 뒤 Image가 사라지지 않도록 저장공간을 따로 준비해야 합니다.
162 | 
163 | ## 3.4 Image 데이터는 어디에 남는가
164 | 
165 | > Harbor Container는 재시작되거나 다시 만들어질 수 있지만, Harbor에 저장한 Image까지 함께 사라지면 안 됩니다.
166 | >
167 | > **그래서**, Image 데이터는 Container 수명과 분리된 저장공간에 두며, 원본 Manual에서는 이 위치를 `data_volume`으로 지정합니다.
168 | >
169 | > `data_volume`은 Image 데이터가 저장될 위치이고 실제 Disk나 Mount와 정상적으로 연결되어야 합니다. 중요한 것은 이름을 외우는 것이 아니라 Harbor를 재시작해도 Repository와 Image가 남는 것입니다.
170 | >
171 | > 실행 위치, FQDN, HTTPS 인증서, Image 저장 위치를 Harbor 설치에 적용하려면 이 값을 하나의 설정 파일에 모아야 합니다.
172 | 
173 | ## 3.5 주요 설치값을 harbor.yml에 모은다
174 | 
175 | > Harbor의 주요 설치값을 모아 두는 파일이 `harbor.yml`입니다.
176 | >
177 | > `hostname`에는 Harbor FQDN, `https.port`에는 HTTPS Port, `certificate`와 `private_key`에는 인증서와 키의 위치, `data_volume`에는 Image 데이터 저장 위치를 지정합니다.
178 | >
179 | > 각 값은 예시를 외우는 것이 아니라 현재 승인된 주소, 실제 파일 경로, Disk와 Mount 상태에 맞는지 확인해야 합니다.
180 | >
181 | > **하지만**, `harbor.yml`을 작성했다고 Harbor가 실행되는 것은 아닙니다. 설치 프로그램이 이 설정을 사용해 Harbor Container를 구성하고 실행해야 합니다.
182 | 
183 | ## 3.6 원본 설치 순서로 연결한다
184 | 
185 | > 실제 설치는 `VM과 Disk → FQDN·DNS·Network → Docker → Offline Installer → Certificate·Private Key·CA → harbor.yml → data_volume → install.sh → Harbor Containers` 순서로 이어집니다.
186 | >
187 | > 이 순서를 통째로 외우기보다 각 단계가 실행 환경, 접속 주소, HTTPS 신뢰, Image 저장 중 어떤 목적을 담당하는지 연결해야 합니다.
188 | >
189 | > **하지만**, `install.sh`가 성공하고 Harbor Container가 Running이라고 해서 실제 사용자가 Harbor를 사용할 수 있다는 뜻은 아닙니다. HTTPS 접속부터 Push와 Pull, 데이터 유지까지 별도로 확인해야 합니다.
190 | 
191 | ---
192 | 
193 | # 4. 설치 성공과 실제 정상은 다르다
194 | 
195 | > `install.sh`가 성공하고 Harbor Container가 Running이면 설치 프로그램이 끝나고 프로세스가 시작됐다는 뜻입니다.
196 | >
197 | > **하지만**, 프로세스가 실행된다는 사실만으로 사용자가 Harbor에 접속하고 Image를 Push하거나 Pull할 수 있다는 뜻은 아닙니다.
198 | >
199 | > Registry API는 Docker나 Worker가 Harbor의 Image 기능과 통신하는 입구입니다. Harbor를 실제로 사용하려면 Web 화면뿐 아니라 이 Registry 기능도 응답해야 합니다.
200 | >
201 | > **그래서**, `HTTPS 접속 → Registry API 응답 → Login → Project 접근 → Test Push → Test Pull → 데이터 저장 → 재시작 후 Repository 유지` 순서로 실제 사용 경로를 확인합니다.
202 | >
203 | > **결국**, **Harbor Container Running과 Harbor 사용 가능 상태는 같지 않습니다.** DNS, 인증서, 권한, Disk 중 하나만 잘못돼도 실제 사용은 실패할 수 있습니다.
204 | >
205 | > Harbor의 실제 사용이 확인돼도 여러 Application 팀이 함께 쓰려면 Image와 권한을 나눌 공간이 필요합니다.
206 | 
207 | ---
208 | 
209 | # 5. 3.2 Create a project — 왜 Harbor 안에 또 공간을 나누는가
210 | 
211 | > Harbor가 실제로 사용 가능한 상태가 되면 여러 Application 팀이 같은 Harbor에 Image를 저장할 수 있습니다.
212 | >
213 | > **하지만**, 모든 팀의 Image를 한 공간에 섞으면 Image의 소유 팀, Push 권한, Storage 사용량을 구분하기 어렵습니다.
214 | >
215 | > **그래서**, Harbor 안에 Application이나 Team별 영역을 나눕니다. 이 영역이 **Harbor Project**이며, Image와 접근 권한을 구분하는 경계입니다.
216 | >
217 | > Project 안에서 실제 Image는 Repository 단위로 정리됩니다.
218 | 
219 | ## 5.1 Repository도 짧게 설명
220 | 
221 | > Harbor는 전체 Registry 서비스이고, Project는 Team이나 Application의 영역이며, Repository는 그 안에서 Image를 저장하는 단위입니다.
222 | >
223 | > Repository에는 실제 Image와 Version을 구분하는 Tag가 연결됩니다. 따라서 `Harbor → Project → Repository → Image와 Tag`의 관계로 이해하면 됩니다.
224 | >
225 | > **하지만**, KubeSphere에서도 Project라는 이름을 사용하므로 두 객체의 역할을 구분해야 합니다.
226 | 
227 | ## 5.2 KubeSphere Project와 비교
228 | 
229 | > **KubeSphere Project**는 Kubernetes에서 Application Resource와 Workload를 운영하는 공간이고, **Harbor Project**는 Container Image와 Repository, 접근 권한을 관리하는 공간입니다.
230 | >
231 | > 이름은 같지만 서로 다른 시스템의 객체이므로 KubeSphere Project가 있다고 Harbor Project가 자동으로 생기지는 않습니다.
232 | >
233 | > **따라서**, Harbor Project 요청은 Kubernetes Project와 별도로 승인 내용과 생성 조건을 확인해야 합니다.
234 | 
235 | ## 5.3 실제 요청에서 Project로 연결
236 | 
237 | > 실제 운영자는 New Project 버튼부터 누르지 않습니다. 먼저 승인된 Project Name, Private 여부, Storage Quota, 사용할 AD 계정과 사용자 구분을 확인합니다.
238 | >
239 | > **하지만**, 오늘 교육에서는 기존 Private Project의 Private, Quota, Member, Role을 읽기 전용으로만 확인합니다. New Project 화면은 절차 설명에 사용할 수 있지만 **Create와 Save는 실행하지 않습니다.**
240 | >
241 | > 실제 운영에서는 승인 내용을 모두 확인한 뒤에만 Harbor Project를 생성합니다.
242 | 
243 | ### Project Name
244 | 
245 | > Project Name은 승인된 이름을 그대로 사용합니다. 임의로 줄이거나 다른 이름으로 만들면 신청 내용과 실제 Image 경로가 달라질 수 있습니다.
246 | 
247 | ### Private
248 | 
249 | > 내부 Application Image는 허용된 사용자만 접근해야 하므로 승인 기준에 따라 Private으로 설정합니다.
250 | 
251 | ### Quota
252 | 
253 | > Quota는 이 Project가 사용할 수 있는 Image 저장공간의 상한입니다. 원본 Manual의 10 GB는 예시이며 실제 승인값을 적용합니다.
254 | >
255 | > **그래서**, 생성 후에는 Project가 화면에 보이는지만 확인하지 않고 Name, Private, Quota가 승인 내용과 일치하는지 확인합니다.
256 | >
257 | > **하지만**, Project를 만들었다고 사용자가 자동으로 접근할 수 있는 것은 아닙니다. AD 사용자를 Member로 연결하고 Role을 부여해야 합니다.
258 | 
259 | ---
260 | 
261 | # 6. 3.3 Managing Users — 공간을 만들었으면 사람을 연결한다
262 | 
263 | > Harbor Project를 만들었다고 모든 사용자가 자동으로 접근할 수 있는 것은 아닙니다.
264 | >
265 | > **그래서**, 실제 AD 사용자를 해당 Project의 Member로 연결하고 그 사용자가 수행할 작업에 맞는 Role을 부여합니다.
266 | >
267 | > Project 접근 권한은 `Project → Member → AD User → Role → 허용된 작업`의 관계로 결정됩니다.
268 | 
269 | ## 6.1 Role의 쉬운 의미
270 | 
271 | > Role은 **이 사용자가 해당 Harbor Project에서 무엇을 할 수 있는가**를 정하는 권한 묶음입니다.
272 | 
273 | ### Developer
274 | 
275 | > Developer는 일반적으로 Image를 Push하고 Pull할 수 있지만 Project의 Member를 관리하지는 않습니다.
276 | 
277 | ### ProjectAdmin
278 | 
279 | > ProjectAdmin은 Image를 Push하고 Pull할 수 있으며 Project의 Member도 관리할 수 있습니다.
280 | >
281 | > **하지만**, Harbor `ProjectAdmin`은 Harbor 안의 Role이며 KubeSphere `project-admin`, `project-operator`와는 다른 권한입니다. 이름이 비슷하다고 같은 Role로 해석하면 안 됩니다.
282 | >
283 | > 신청서의 Admin과 User를 Harbor Role에 연결할 때도 이름만 보고 자동으로 확정할 수 없습니다.
284 | 
285 | ## 6.2 신청서 Admin/User를 바로 확정하지 않는다
286 | 
287 | > 원본 신청 양식에는 Admin과 User가 있고 Harbor에는 ProjectAdmin과 Developer가 있습니다. 역할 의미만 보면 관리가 필요한 사용자는 ProjectAdmin, 일반 Image 사용자는 Developer 방향으로 이해할 수 있습니다.
288 | >
289 | > **하지만**, 신청서 Permission과 Harbor Role의 최종 매핑은 Xi'an 승인 운영 정책을 기준으로 확정해야 합니다.
290 | >
291 | > **그래서**, 사용자가 Member 관리까지 필요한지 아니면 Image Push와 Pull만 필요한지 확인하고, 승인된 Role 정책에 따라 ProjectAdmin 또는 Developer를 적용합니다.
292 | >
293 | > 강사의 기억이나 화면의 이름만으로 Role을 임의 지정하지 않습니다.
294 | 
295 | ## 6.3 Login 성공과 Project 권한은 다르다
296 | 
297 | > Harbor Login 성공은 Harbor가 해당 사용자의 Account와 인증정보를 확인했다는 뜻입니다.
298 | >
299 | > **하지만**, 인증 성공이 모든 Private Project의 사용 권한을 의미하지는 않습니다. 특정 Project에서 Image를 Push하거나 Pull하려면 그 Project의 Member여야 하고 적절한 Role도 가져야 합니다.
300 | >
301 | > **그래서**, Login은 되는데 Push가 거부되면 비밀번호만 다시 확인하지 않습니다. 대상 Project, Member 여부, Role, Repository와 Tag, Quota를 순서대로 구분해서 확인합니다.
302 | >
303 | > Project 생성과 User 권한 부여는 실제 운영 요청 안에서 하나의 흐름으로 연결됩니다.
304 | 
305 | ---
306 | 
307 | # 7. 3.2~3.3을 실제 반복 운영 요청으로 연결한다
308 | 
309 | > 새로운 Application 팀이 Harbor에 Image를 보관할 공간과 사용자 권한을 요청했다고 하겠습니다.
310 | >
311 | > 먼저 승인 내용에서 Project Name, Private 여부, Storage Quota, AD 사용자, 관리자와 일반 사용자 구분, 승인된 Role 정책을 확인합니다.
312 | >
313 | > **그래서**, 실제 반복 운영은 `승인 내용 확인 → Harbor Project 생성 → Member 추가 → Role 적용 → Login과 Push·Pull 권한 확인` 순서로 진행합니다.
314 | >
315 | > **하지만**, Project가 화면에 보이거나 Member가 추가됐다는 사실만으로 요청이 완료된 것은 아닙니다. 승인값과 실제 설정이 일치하고 해당 사용자가 허용된 작업을 수행할 수 있어야 합니다.
316 | >
317 | > 3.1 Harbor Installation은 이 요청마다 다시 수행하는 작업이 아니라, Project와 User 운영이 올라가 있는 플랫폼 기반입니다.
318 | >
319 | > 사용자가 Harbor에 Image를 Push한 뒤에는 Kubernetes가 그 Private Image를 가져오는 별도의 경로가 이어집니다.
320 | 
321 | ---
322 | 
323 | # 8. Private Harbor Image를 Kubernetes가 사용하는 경로
324 | 
325 | > Developer나 CI가 Harbor에 Image를 Push하면 Image는 Harbor Repository에 저장됩니다.
326 | >
327 | > **하지만**, Harbor Project가 Private이면 Kubernetes도 인증 없이 그 Image를 가져올 수 없습니다.
328 | >
329 | > Kubernetes에는 Harbor 인증정보를 담은 `Registry Secret`이 필요하고, Workload는 `imagePullSecrets`와 정확한 Image 주소를 사용해야 합니다.
330 | >
331 | > 전체 경로는 `Developer·CI Login → Harbor Push → Repository 저장 → Kubernetes 인증정보 → Image 주소 지정 → Worker Pull → Container와 Pod 실행`으로 이어집니다.
332 | >
333 | > 오늘은 `Registry Secret`과 `imagePullSecrets`의 생성 절차까지 실행하지 않고, 해당 절차는 다음 User Manual에서 다룹니다.
334 | >
335 | > **결국**, Private Harbor에서는 Worker가 아무 인증 없이 Image를 자동으로 Pull하지 않습니다. 이 경로의 어느 단계가 실패했는지에 따라 확인할 장애 지점도 달라집니다.
336 | 
337 | ---
338 | 
339 | # 9. 장애도 쉬운 질문부터 본다
340 | 
341 | > 장애는 보이는 증상에 따라 확인 시작점이 달라집니다. 화면 접근, HTTPS 신뢰, 사용자 인증, Project 권한, Kubernetes Pull 경로를 섞지 않고 처음 끊긴 단계부터 확인합니다.
342 | 
343 | ## 9.1 Harbor 화면 자체가 안 열린다
344 | 
345 | > Harbor 화면 자체가 열리지 않으면 Login이나 Project 권한보다 앞선 접속 경로에서 요청이 끊긴 것입니다.
346 | >
347 | > **그래서**, FQDN을 DNS가 찾는지, Network와 Firewall 경로가 열렸는지, HTTPS Port에 접근할 수 있는지, Harbor Container가 실행 중인지 순서대로 확인합니다.
348 | >
349 | > 서버에는 도달했지만 x509 오류가 보인다면 접속 경로가 아니라 HTTPS 신뢰 단계로 이동합니다.
350 | 
351 | ## 9.2 Web은 열리는데 x509
352 | 
353 | > x509 오류는 Client가 Harbor 서버에는 도달했지만 해당 Server Certificate의 신뢰를 완성하지 못했다는 뜻입니다.
354 | >
355 | > **그래서**, 접속한 FQDN과 Server Certificate가 일치하는지, 인증서 Chain이 완전한지, Client가 Root와 Intermediate CA를 신뢰하는지 확인합니다.
356 | >
357 | > 이 단계에서는 Account와 Password보다 인증서 신뢰를 먼저 해결해야 합니다. HTTPS가 정상인데 Login이 실패하면 사용자 인증을 확인합니다.
358 | 
359 | ## 9.3 Login 실패
360 | 
361 | > Network와 HTTPS가 정상인데 Login이 실패하면 Account, Password, AD 상태, Harbor 인증 연동을 확인합니다.
362 | >
363 | > **하지만**, Login 성공은 사용자 인증까지만 증명하며 특정 Project의 Push와 Pull 권한까지 보장하지는 않습니다.
364 | 
365 | ## 9.4 Login은 되는데 Push denied
366 | 
367 | > Login은 성공했지만 Push가 거부되면 사용자 인증을 반복하지 않고 Project 권한 경로를 확인합니다.
368 | >
369 | > 대상 Project가 맞는지, 사용자가 Member인지, Role에 Push 권한이 있는지, Repository와 Tag가 올바른지, Quota가 남아 있는지 순서대로 봅니다.
370 | >
371 | > **그래서**, 이 증상에서 비밀번호 변경을 첫 조치로 삼지 않습니다. Harbor 사용자의 Push가 성공해도 Kubernetes Worker의 Pull은 별도 경로입니다.
372 | 
373 | ## 9.5 Harbor에는 Image가 있는데 Kubernetes Pull 실패
374 | 
375 | > Harbor에 Image가 있고 사용자의 Push가 성공했다는 사실은 Developer에서 Harbor까지의 경로가 정상이라는 뜻입니다. Kubernetes Worker가 같은 Image를 Pull하는 경로는 따로 확인해야 합니다.
376 | >
377 | > Image 주소와 Tag, `Registry Secret`과 `imagePullSecrets`, Worker의 DNS·Network·인증서 신뢰·Pull 권한, Pod Event를 확인합니다.
378 | >
379 | > **그래서**, 먼저 Pod Event에서 실제 Pull 오류를 확인한 뒤 Image 경로부터 Worker 접근까지 첫 단절 지점을 찾습니다.
380 | >
381 | > Secret 생성과 연결의 상세 절차는 다음 User Manual에서 다루지만, Push 성공과 Worker Pull 성공이 다른 검증 단계라는 점은 여기서 구분합니다.
382 | 
383 | ---
384 | 
385 | # 10. 마무리 — 기술 용어보다 이야기로 다시 말한다
386 | 
387 | > 오늘 Harbor에서 가장 중요한 것은 메뉴와 기술 이름을 외우는 것이 아니라 Image가 만들어지고 저장되고 사용되는 전체 흐름을 이해하는 것입니다.
388 | >
389 | > Application을 실행하려면 Container Image가 필요하고, 여러 Worker가 같은 Image를 사용하려면 중앙 Registry가 필요합니다. Xi'an에서는 Harbor가 이 Registry 역할을 담당합니다.
390 | >
391 | > Harbor 플랫폼은 실행 서버, FQDN과 접속 경로, HTTPS 인증서 신뢰, Image를 유지할 저장공간 위에서 동작합니다.
392 | >
393 | > **하지만**, Harbor 자체가 정상이라는 사실만으로 여러 팀의 Image와 권한이 자동으로 구분되지는 않습니다.
394 | >
395 | > **그래서**, Application별 Harbor Project를 만들고 Name, Private, Quota를 승인 내용에 맞춘 뒤 AD 사용자를 Member로 연결하고 Role을 부여합니다.
396 | >
397 | > Image가 Harbor에 Push된 뒤 Kubernetes가 Private Image를 사용하려면 Registry 인증정보와 정확한 Image 주소가 필요하며, Worker가 Image를 Pull해야 Pod와 Container가 실행됩니다.
398 | >
399 | > **결국**, `Image → Registry → Harbor 기반 → Project → Member와 Role → Push와 Pull → Kubernetes 인증 → Worker Pull → Pod 실행`의 전체 경로를 구분하고 각 단계의 실제 성공을 확인해야 합니다.
400 | 
401 | ---
402 | 
403 | # 11. 마지막 확인 질문
404 | 
405 | 기술 이름만 외웠는지 묻지 않고, 문제와 역할을 설명할 수 있는지 순서대로 확인한다.
406 | 
407 | 1. Application을 같은 조건으로 실행하려면 프로그램 외에 무엇을 함께 준비해야 하는가?
408 | 2. Image와 Container는 무엇이 다르고, Kubernetes에서는 Container가 어디에서 실행되는가?
409 | 3. Worker가 여러 대일 때 Image를 직접 복사하면 어떤 문제가 생기며, 중앙 저장소가 왜 필요한가?
410 | 4. Registry는 어떤 역할이고 Xi'an에서는 어떤 제품이 그 역할을 담당하는가?
411 | 5. Harbor에 Image를 넣고 가져오는 동작은 각각 무엇인가?
412 | 6. 3.1 Installation, 3.2 Create a project, 3.3 Managing Users는 실제 업무에서 어떻게 구분되는가?
413 | 7. Harbor를 구축할 때 실행 환경, 접속 주소, HTTPS 신뢰, Image 저장공간을 각각 왜 확인해야 하는가?
414 | 8. Harbor Container가 Running이어도 실제 사용 가능 상태라고 확정할 수 없는 이유는 무엇인가?
415 | 9. Harbor Project가 왜 필요하고 KubeSphere Project와 무엇이 다른가?
416 | 10. Developer와 ProjectAdmin은 무엇이 다르며 신청서 사용자를 Role에 연결할 때 무엇을 기준으로 해야 하는가?
417 | 11. Login은 되지만 Push가 거부될 때 인증정보 외에 무엇을 확인해야 하는가?
418 | 12. Kubernetes가 Private Harbor Image를 Pull하려면 어떤 인증정보와 설정이 추가로 필요한가?
419 | 
420 | ---
421 | 
422 | # 원본 Manual 바로가기
423 | 
424 | - [[50. 운영/06. Harbor Manual/01. Harbor Installation|3.1 Harbor Installation]]
425 | - [[50. 운영/06. Harbor Manual/02. Create a project|3.2 Create a project]]
426 | - [[50. 운영/06. Harbor Manual/03. Managing Users|3.3 Managing Users]]
427 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오전/01. Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본.md

Bytes: 13506
SHA-256: 28ef2ee8e9078f924150ce0d302fc437f200aea9d932b2d92696d5a65de9cdf4
Lines: 1-391 of 391

```markdown
  1 | ---
  2 | title: "Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-01 Xi'an 신규 Member 구축 2일차 오전 - 8월 31일 GO 재확인, Kubespray 실행, 최초 실패와 recap 판독"
  6 | created: "2026-08-27"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 8월 31일에 검증한 신규 Member 입력을 실제 Kubespray 실행으로 넘길 때 **무엇을 다시 확인하고, 실행 로그에서 어떤 실패를 먼저 믿으며, 언제 재실행해도 되는지 판단하는 법**을 가르친다. 정확한 Kubespray 옵션·세부 Role·복구 절차는 원본 Runbook을 따른다. 오늘 오전의 목표는 명령 암기가 아니라 **올바른 입력으로 한 번 실행하고, 실패가 있으면 최초 단절을 증거로 좁혀 같은 대상을 다시 검증하는 것**이다.
 14 | 
 15 | ## 0. 8월 31일에서 이어받는 것
 16 | 
 17 | 어제 마지막 블록에서 이미 다음을 판정했다.
 18 | 
 19 | ```text
 20 | 신규 Member Cluster Identity
 21 | + Bastion Identity
 22 | + Bundle·Kubespray 기준
 23 | + hosts.yaml Host·Group
 24 | + VIP·CIDR·Domain
 25 | + Registry·Version
 26 | + Ansible Graph·Ping·Identity·Become
 27 | + Syntax Check
 28 | = GO 또는 BLOCKED
 29 | ```
 30 | 
 31 | > 오늘은 어제의 모든 Preflight를 처음부터 반복하지 않습니다. 대신 **실행을 결정하는 핵심 증거가 지금도 같은 대상과 같은 내용인지** 확인합니다.
 32 | 
 33 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 34 | 
 35 | > `cluster.yml`을 실행하기 전에 8월 31일 GO가 현재도 유효한지 확인하고, 실행 중 문제가 생기면 **어느 Host의 어느 Task가 최초로 실패했는지**, 그 실패가 `UNREACHABLE`인지 Task `FAILED`인지, 이후 오류가 연쇄 결과인지 구분한 뒤 재실행 여부를 판단할 수 있어야 한다.
 36 | 
 37 | 오늘의 중심 질문은 하나다.
 38 | 
 39 | > **지금 이 입력으로 이 신규 Member에 Kubespray를 실행해도 되는가? 실패했다면 최초 실패가 정확히 무엇을 증명하는가?**
 40 | 
 41 | ---
 42 | 
 43 | # 1. 시작 — 오늘 만드는 것은 Playbook 성공 화면이 아니다
 44 | 
 45 | > 오늘 오전에는 실제 신규 Member Kubernetes Cluster 설치를 시작합니다.
 46 | >
 47 | > 하지만 목표를 `ansible-playbook` 명령이 끝나는 것으로 잡지 않습니다. Kubespray는 우리가 준 Inventory와 변수 값을 믿고 여러 Node에 빠르게 변경을 적용합니다.
 48 | >
 49 | > 잘못된 IP가 실제 다른 Server를 가리키고 있다면 연결도 성공하고 많은 Task도 성공할 수 있습니다. 따라서 자동화의 힘은 입력이 맞을 때만 장점입니다.
 50 | 
 51 | Kubespray 실행을 다음처럼 이해한다.
 52 | 
 53 | ```text
 54 | 8월 31일에 확인한 현실
 55 | → Inventory·변수로 표현
 56 | → Kubespray가 그 입력을 읽음
 57 | → Host별 Task 수행
 58 | → Kubernetes Component 구성
 59 | → 이후 기능 검증이 가능한 상태
 60 | ```
 61 | 
 62 | > **오늘 오전의 완료는 Cluster 정상 완료가 아닙니다.** 실행이 미해결 자동화 오류 없이 끝나고, 오후 기능 검증을 시작할 수 있는 상태가 되는 것입니다.
 63 | 
 64 | ---
 65 | 
 66 | # 2. GO를 다시 실행 허가로 바꾸기 전에 현재성을 확인한다
 67 | 
 68 | > 8월 31일에 GO였다는 사실은 어제 그 시점의 증거입니다. 밤사이 VM, 파일, Bundle, Registry, 승인 시간이 바뀌었을 수 있습니다.
 69 | 
 70 | 다시 확인할 것은 전체 Preflight가 아니라 실행을 바꾸는 항목이다.
 71 | 
 72 | ```text
 73 | 현재 Bastion Hostname·IP
 74 | 현재 작업 Account
 75 | 현재 Bundle Root·Kubespray Directory
 76 | 현재 hosts.yaml·주요 변수 파일
 77 | 현재 Registry·Kubernetes Version
 78 | 현재 Inventory Graph의 Host·Group
 79 | 현재 Ansible Ping·Identity·Become
 80 | 현재 실행 승인·유지보수 시간
 81 | ```
 82 | 
 83 | ## 2.1 GO의 의미
 84 | 
 85 | ```text
 86 | 8월 31일 GO
 87 | = 실행 전 필수 입력과 연결이 당시 증거로 통과
 88 | ```
 89 | 
 90 | 하지만:
 91 | 
 92 | ```text
 93 | 8월 31일 GO
 94 | ≠ 9월 1일 현재 파일과 환경이 자동으로 동일
 95 | ```
 96 | 
 97 | 따라서 핵심 파일이 변경됐다면 그 변경이 승인된 것인지 확인한다.
 98 | 
 99 | > 미확정 VIP, CIDR, ETCD Filesystem, Repository, Registry, Credential 같은 **실행 필수값이 새로 불명확해졌다면 다시 BLOCKED**입니다. 시간을 맞추기 위해 추측값을 넣지 않습니다.
100 | 
101 | ## 2.2 실행 전 마지막 말하기 Gate
102 | 
103 | 강사는 실행 직전 수강생에게 다음을 말하게 한다.
104 | 
105 | ```text
106 | 어느 Cluster를 만드는가
107 | 어느 Bastion에서 실행하는가
108 | 어느 Inventory를 읽는가
109 | 어느 Bundle·Kubespray를 사용하는가
110 | VIP·CIDR·Domain·Registry·Version의 근거는 무엇인가
111 | 실행 승인 시간은 언제인가
112 | 로그는 어디에 남길 것인가
113 | ```
114 | 
115 | > 이 답이 한 신규 Member를 가리키지 않으면 실행하지 않습니다.
116 | 
117 | ---
118 | 
119 | # 3. 실행 명령은 하나의 canonical 구조로만 본다
120 | 
121 | 오늘 실제 실행 구조는 현재 승인된 Runbook을 따른다.
122 | 
123 | 대표 구조:
124 | 
125 | ```bash
126 | ansible-playbook \
127 |   -e @inventory/dks/dks_vars.yml \
128 |   -i inventory/dks/hosts.yaml \
129 |   --become --become-user=root \
130 |   cluster.yml
131 | ```
132 | 
133 | > 실제 경로·추가 옵션·Ansible Config는 현재 Bundle과 Runbook을 우선합니다. 이 대본에서 임의의 재실행 옵션이나 우회 옵션을 만들지 않습니다.
134 | 
135 | 실행 전 기록할 최소 정보:
136 | 
137 | ```text
138 | Cluster Name·Stage
139 | Bastion Hostname
140 | Bundle Root·Version
141 | Inventory 위치·Checksum
142 | 주요 변수 파일 Checksum
143 | 실행 시작 시각
144 | 실행 Account
145 | 승인자·작업 시간
146 | 로그 파일 위치
147 | ```
148 | 
149 | > Password, SSH Private Key, Registry Credential, Token은 기록하지 않습니다.
150 | 
151 | ---
152 | 
153 | # 4. Playbook 로그는 ‘어디에서 처음 달라졌는가’를 찾는 자료다
154 | 
155 | > 로그가 길다고 처음부터 모든 줄을 분석하지 않습니다. 먼저 **정상 진행이 어디까지 이어졌고 최초 비정상이 어디에서 시작했는지** 찾습니다.
156 | 
157 | 최초로 고정할 네 가지:
158 | 
159 | ```text
160 | 어느 Host인가
161 | 어느 Task인가
162 | UNREACHABLE인가 FAILED인가
163 | 한 Host만인가 여러 Host 공통인가
164 | ```
165 | 
166 | 그리고 마지막에 PLAY RECAP을 본다.
167 | 
168 | ```text
169 | ok
170 | changed
171 | unreachable
172 | failed
173 | skipped
174 | rescued
175 | ignored
176 | ```
177 | 
178 | ## 4.1 `UNREACHABLE`과 `FAILED`는 조사 시작점이 다르다
179 | 
180 | ```text
181 | UNREACHABLE
182 | → Ansible이 대상 Host에서 Task 자체를 시작하지 못한 경계
183 | → Hostname·IP·DNS·Network·SSH·Account를 먼저 봄
184 | 
185 | FAILED
186 | → 대상 Host에 도달해 Task를 실행했지만 작업 또는 검증이 실패한 경계
187 | → 해당 Task 입력·현재 상태·권한·Package·Service·설정 등을 봄
188 | ```
189 | 
190 | > `UNREACHABLE`을 Kubernetes 설치 문제로 바로 부르지 않습니다. 아직 원격 Task를 실행하지 못한 것입니다.
191 | 
192 | ## 4.2 첫 FAILED와 뒤의 FAILED를 구분한다
193 | 
194 | 예를 들어 초기 Package 설치가 실패하면 뒤의 Kubernetes Component Task도 연쇄적으로 실패할 수 있다.
195 | 
196 | ```text
197 | 최초 FAILED
198 | → 다음 정상 경로를 처음 끊은 후보
199 | 
200 | 뒤의 다수 FAILED
201 | → 최초 실패의 결과일 수 있음
202 | ```
203 | 
204 | > Recap에 `failed=20`이 보인다고 원인이 20개라는 뜻은 아닙니다.
205 | 
206 | ---
207 | 
208 | # 5. 실패가 나면 먼저 ‘같은 실패’를 증명한다
209 | 
210 | > 로그 한 줄만 보고 바로 설정을 바꾸지 않습니다.
211 | 
212 | 먼저 대상과 오류를 고정한다.
213 | 
214 | ```text
215 | 실패 Host
216 | 실패 Task
217 | 오류 원문
218 | Task가 사용한 주요 입력
219 | 같은 Role의 정상 Host가 있는지
220 | 직전 Task까지 성공했는지
221 | ```
222 | 
223 | 그다음 다음 질문을 한다.
224 | 
225 | > **어떤 읽기 전용 확인 하나가 다음 행동을 바꿀 것인가?**
226 | 
227 | 대표 예:
228 | 
229 | | 실패 | 다음 첫 확인 |
230 | |---|---|
231 | | UNREACHABLE | Inventory Hostname·IP와 실제 DNS·SSH 경로 |
232 | | sudo/become 실패 | 같은 Account의 `sudo -n` 기능 |
233 | | Package 설치 실패 | 승인 Repo·OS Version·Package 존재 |
234 | | Registry/Image 실패 | 실제 Image 주소·Registry 접근·CA Trust |
235 | | kubelet/Service 시작 실패 | Service 상태와 해당 Task가 만든 설정 |
236 | | 특정 Role만 실패 | 정상 Role과의 차이보다 같은 Role 정상 Host와 먼저 비교 |
237 | 
238 | > 원인과 무관한 영역을 동시에 바꾸지 않습니다. 여러 설정을 한꺼번에 바꾸면 어느 변경이 결과를 만들었는지 증명할 수 없습니다.
239 | 
240 | ---
241 | 
242 | # 6. 재실행은 ‘처음부터 다시’가 아니라 적용 상태를 이해한 뒤 한다
243 | 
244 | Ansible과 Kubespray는 많은 Task가 반복 실행 가능한 구조를 갖지만, 이것이 무조건 안전한 재실행을 뜻하지는 않는다.
245 | 
246 | 반드시 구분한다.
247 | 
248 | ```text
249 | Playbook 재실행 가능성
250 | ≠ 현재 부분 적용 상태를 무시해도 됨
251 | ```
252 | 
253 | 재실행 전에 최소한 다음을 확인한다.
254 | 
255 | ```text
256 | 최초 실패 원인이 무엇이었는가
257 | 어떤 조치를 했는가
258 | 조치 후 좁은 기능 확인이 성공했는가
259 | 이미 적용된 변경은 무엇인가
260 | 현재 Inventory·변수가 처음 실행과 같은가
261 | 재실행 범위와 영향이 Runbook 기준에 맞는가
262 | ```
263 | 
264 | > 첫 실패가 해소됐는지 확인하지 않고 같은 명령을 반복해 로그가 달라지기만 기다리지 않습니다.
265 | 
266 | ## 6.1 좁은 확인이 먼저다
267 | 
268 | 예:
269 | 
270 | ```text
271 | SSH 문제를 고쳤다
272 | → 해당 Host의 SSH·Ansible Ping 먼저 확인
273 | → 전체 cluster.yml 재실행은 그 뒤
274 | 
275 | Repository 문제를 고쳤다
276 | → 해당 Host에서 Metadata·필수 Package 조회 먼저 확인
277 | → 전체 재실행은 그 뒤
278 | ```
279 | 
280 | 이 원칙은 하루 전체에서 계속 사용한다.
281 | 
282 | ---
283 | 
284 | # 7. 실행 완료의 증거 범위를 정확히 제한한다
285 | 
286 | 오전 실행 PASS는 다음을 의미한다.
287 | 
288 | ```text
289 | 승인된 신규 Member 입력으로 cluster.yml 실행
290 | + 최종 Return Code 정상
291 | + PLAY RECAP에 미해결 failed·unreachable 없음
292 | + 실행 로그와 입력 기준이 보존됨
293 | ```
294 | 
295 | 하지만 아직 다음은 증명하지 않았다.
296 | 
297 | ```text
298 | API 기능 정상
299 | Node Identity·Role·Ready 정상
300 | Control Plane 기능 정상
301 | ETCD 상태 정상
302 | 실제 Pod Network 정상
303 | Cluster DNS 질의 정상
304 | Ingress·VIP-B 사용자 경로 정상
305 | Storage 정상
306 | ```
307 | 
308 | 즉:
309 | 
310 | ```text
311 | PLAYBOOK EXECUTION PASS
312 | ≠ KUBERNETES BASE PASS
313 | ```
314 | 
315 | > 오전 성공을 오후 전체 기능 성공으로 확대하지 않습니다.
316 | 
317 | ---
318 | 
319 | # 8. 실행이 끝나면 ‘어제 입력 → 오늘 결과’ 연결을 남긴다
320 | 
321 | 오후 검증으로 넘길 최소 증거:
322 | 
323 | ```text
324 | Cluster Name·Stage
325 | 현재 kubeconfig 후보와 검증 Account
326 | Bastion·Bundle 기준
327 | Inventory·주요 변수 Checksum
328 | Kubernetes Version 기대값
329 | VIP-A·Pod CIDR·Service CIDR·Domain 기대값
330 | Node Role·Hostname·IP 기대표
331 | 최종 cluster.yml 실행 시각
332 | Return Code
333 | PLAY RECAP
334 | 실행 로그 위치
335 | 재실행이 있었다면 최초 실패·조치·재검증 기록
336 | 남은 미확정 또는 비차단 관찰사항
337 | ```
338 | 
339 | > 오후에는 이 값을 다시 처음부터 만드는 것이 아니라, **8월 31일에 입력한 설계가 실제 Kubernetes로 만들어졌는지** 대조합니다.
340 | 
341 | ---
342 | 
343 | # 9. 오전 BLOCKED 기준
344 | 
345 | 다음 중 하나가 남으면 기능 검증을 정상 흐름으로 시작하지 않고 실행 문제부터 닫는다.
346 | 
347 | ```text
348 | 현재 대상 Cluster·Bastion·Inventory 불일치
349 | 실행 필수값 미확정
350 | 실행 승인·작업 시간 없음
351 | 미해결 UNREACHABLE 존재
352 | 미해결 FAILED 존재
353 | Return Code 비정상
354 | 재실행 후에도 최초 실패 원인 미확정
355 | 로그와 실제 입력 기준을 연결할 수 없음
356 | ```
357 | 
358 | > BLOCKED를 숨기기 위해 `failed`를 ignore하거나 임의 옵션을 추가하지 않습니다.
359 | 
360 | ---
361 | 
362 | # 10. 마무리 — Kubespray 실행을 한 문장으로 다시 말한다
363 | 
364 | > Kubespray는 Cluster가 맞는지 판단해 주는 도구가 아니라, 우리가 제공한 Inventory와 변수에 따라 여러 Node를 자동으로 구성하는 도구입니다.
365 | >
366 | > 그래서 실행 전에는 8월 31일 GO가 현재도 같은 대상인지 확인하고, 실행 중에는 긴 로그에서 최초 실패 Host와 Task를 고정합니다.
367 | >
368 | > 실패가 있으면 원인을 추정해 여러 설정을 바꾸지 않고 다음 행동을 바꾸는 최소 확인부터 합니다. 재실행은 그 원인과 적용 상태를 이해한 뒤 승인된 동일 경로로 수행합니다.
369 | >
370 | > **결국 오전의 성공은 Playbook이 미해결 자동화 오류 없이 끝났다는 뜻이며, 실제 Kubernetes가 정상이라는 판정은 오후 기능 검증에서 별도로 해야 합니다.**
371 | 
372 | ---
373 | 
374 | # 11. 마지막 Teach-back
375 | 
376 | 1. 8월 31일 GO를 9월 1일 실행 직전에 그대로 믿지 않고 다시 현재성을 확인해야 하는 이유는 무엇인가?
377 | 2. `UNREACHABLE`과 Task `FAILED`는 무엇이 다르며 조사 시작점은 어떻게 다른가?
378 | 3. PLAY RECAP에 여러 FAILED가 있어도 최초 FAILED를 먼저 찾는 이유는 무엇인가?
379 | 4. 실패 후 바로 전체 Playbook을 반복하지 않고 좁은 기능 확인을 먼저 해야 하는 이유는 무엇인가?
380 | 5. Return Code 0과 Kubernetes 기능 정상은 왜 다른 증거인가?
381 | 6. 오전 실행 PASS가 오후 검증으로 넘겨야 할 최소 증거는 무엇인가?
382 | 
383 | ---
384 | 
385 | # 기준 문서 바로가기
386 | 
387 | - [[출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증|2026-09-01 Member 구축 2일차 기준]]
388 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
389 | - [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
390 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
391 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오후/01. Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본.md

Bytes: 14706
SHA-256: ceddf9f4076a26687d210deb97f0173c76d0e7ee3dd4606cc774da5e262685eb
Lines: 1-502 of 502

```markdown
  1 | ---
  2 | title: "Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-01 Xi'an 신규 Member 구축 2일차 오후 - Cluster Identity, API·VIP-A, 전역 설계값, Node·Control Plane 검증"
  6 | created: "2026-08-27"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 오전 Kubespray 실행이 미해결 자동화 오류 없이 끝난 뒤, **8월 31일에 입력한 신규 Member 설계가 실제 Kubernetes Control Path로 만들어졌는지 증명하는 법**을 가르친다. `kubectl` 명령을 외우는 것이 목적이 아니다. 같은 신규 Member Context에서 **API → 실제 전역값 → Node Identity·Role·Ready → Control Plane**을 독립 증거로 확인하고 다음 Data Plane 검증으로 넘기는 것이 목적이다.
 14 | 
 15 | ## 0. 오전에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage
 19 | Bastion·Bundle 기준
 20 | Inventory·주요 변수 Checksum
 21 | Kubernetes Version 기대값
 22 | VIP-A 기대값
 23 | Pod CIDR·Service CIDR·Domain 기대값
 24 | Node Role·Hostname·IP 기대표
 25 | 최종 cluster.yml Return Code·PLAY RECAP
 26 | 실행 로그
 27 | 최초 실패·조치·재검증 기록
 28 | ```
 29 | 
 30 | > 오후에는 이 값을 다시 만들어내지 않습니다. **이 값이 실제 Cluster에 어떻게 반영됐는지 확인합니다.**
 31 | 
 32 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 33 | 
 34 | > `kubectl get nodes` 한 화면만 보고 설치 완료를 선언하지 않고, **현재 kubeconfig가 신규 Member를 가리키는지 → VIP-A API가 실제 응답하는지 → 전역 설계값이 입력과 같은지 → 예상 Node가 올바른 Role·IP·Version으로 등록되고 Ready인지 → Control Plane 핵심 Component가 기능하는지**를 구분해서 판정할 수 있어야 한다.
 35 | 
 36 | 오늘의 중심 질문:
 37 | 
 38 | > **8월 31일에 입력한 신규 Member 설계가 실제 Kubernetes Control Path로 만들어졌는가?**
 39 | 
 40 | ---
 41 | 
 42 | # 1. 시작 — `kubectl` 성공보다 어느 Cluster에 묻고 있는지가 먼저다
 43 | 
 44 | > 오전에는 Kubespray가 신규 Member Node에 Kubernetes를 설치했습니다.
 45 | >
 46 | > 이제 사람이 Cluster에 질문합니다. `kubectl`은 Node 파일을 직접 읽는 도구가 아니라 Kubernetes API Server에 요청을 보내는 Client입니다.
 47 | >
 48 | > 따라서 결과가 그럴듯한가보다 **어느 kubeconfig의 어느 Context가 어느 API Server를 가리키는가**가 먼저입니다.
 49 | 
 50 | 정상 요청 경로:
 51 | 
 52 | ```text
 53 | 운영자
 54 | → kubectl
 55 | → kubeconfig
 56 | → current-context
 57 | → 신규 Member API Endpoint
 58 | → kube-apiserver
 59 | → Resource 응답
 60 | ```
 61 | 
 62 | 반드시 구분한다.
 63 | 
 64 | ```text
 65 | kubectl Binary 존재
 66 | ≠ 신규 Member 접근 준비
 67 | 
 68 | current-context 표시
 69 | ≠ 신규 Member Context
 70 | 
 71 | Resource 응답 성공
 72 | ≠ VIP-A 경로까지 정상
 73 | ```
 74 | 
 75 | ---
 76 | 
 77 | # 2. 검증 대상을 하나로 고정한다
 78 | 
 79 | 먼저 기록한다.
 80 | 
 81 | ```text
 82 | 검증 Cluster Name·Stage: ________________________________
 83 | 현재 kubeconfig: _________________________________________
 84 | current-context: _________________________________________
 85 | API Server URL: __________________________________________
 86 | VIP-A 기대값: ____________________________________________
 87 | Kubernetes Version 기대값: _______________________________
 88 | Pod CIDR 기대값: _________________________________________
 89 | Service CIDR 기대값: _____________________________________
 90 | Domain 기대값: ___________________________________________
 91 | Node 기대표 위치: ________________________________________
 92 | 오전 실행 Log·Recap: _____________________________________
 93 | ```
 94 | 
 95 | 기본 확인 예:
 96 | 
 97 | ```bash
 98 | kubectl config current-context
 99 | kubectl config view --minify
100 | ```
101 | 
102 | > kubeconfig에는 Credential이 포함될 수 있으므로 원문 전체를 교육 증적에 복사하지 않습니다. Cluster Name, Server URL, Context 같은 판정 정보만 승인된 방식으로 확인합니다.
103 | 
104 | ## 2.1 다른 Cluster에서의 성공은 증거가 아니다
105 | 
106 | ```text
107 | 기존 PRD Member kubectl 성공
108 | ≠ 신규 Member API 성공
109 | 
110 | Master 직접 API 성공
111 | ≠ VIP-A 경로 성공
112 | ```
113 | 
114 | > 검증 중 Context가 바뀌면 뒤 결과를 같은 증거 묶음으로 사용하지 않습니다.
115 | 
116 | ---
117 | 
118 | # 3. API는 직접 경로와 VIP-A 경로를 구분한다
119 | 
120 | > API Server가 Master에서 동작하는 것과 운영자·Bastion이 VIP-A를 통해 접근하는 것은 서로 다른 경로입니다.
121 | 
122 | 개념적으로:
123 | 
124 | ```text
125 | Master 내부 또는 직접 경로
126 | → kube-apiserver 자체 기능
127 | 
128 | 운영자·Bastion
129 | → VIP-A:6443
130 | → Master API Backend
131 | ```
132 | 
133 | ## 3.1 API 응답과 준비 상태
134 | 
135 | 대표적인 읽기 전용 확인은 현재 승인 Runbook을 따른다.
136 | 
137 | 예:
138 | 
139 | ```bash
140 | kubectl get --raw='/readyz?verbose'
141 | ```
142 | 
143 | 또는 승인된 API health 확인 경로를 사용한다.
144 | 
145 | 증거 범위:
146 | 
147 | ```text
148 | readyz 정상
149 | = 현재 kubeconfig가 가리키는 API가 주요 readiness check를 통과
150 | ```
151 | 
152 | 하지만:
153 | 
154 | ```text
155 | readyz 정상
156 | ≠ Node 전체 정상
157 | ≠ ETCD·CNI·DNS·Ingress 실제 기능 전체 정상
158 | ```
159 | 
160 | ## 3.2 VIP-A 자체를 증명한다
161 | 
162 | > kubeconfig의 Server URL이 VIP-A인지 확인하고, 8월 31일 승인값과 대조합니다. Master 개별 IP를 가리키는 임시 kubeconfig로 성공한 결과를 VIP-A HA 경로의 증거로 확대하지 않습니다.
163 | 
164 | CONTROL PATH에서 VIP-A가 틀리면 다음 단계로 넘기지 않는다.
165 | 
166 | ---
167 | 
168 | # 4. 전역 설정 — 입력 파일이 실제 Cluster에 반영됐는가
169 | 
170 | > 이제 8월 31일에 넣은 설계값이 실제 Cluster 설정으로 만들어졌는지 확인합니다.
171 | 
172 | 최소 대조 항목:
173 | 
174 | ```text
175 | Control Plane Endpoint / VIP-A
176 | Kubernetes Version
177 | Cluster Name 또는 식별 기준
178 | Pod CIDR
179 | Service CIDR
180 | Cluster DNS Domain
181 | 필요한 Node CIDR 관련 설정
182 | ```
183 | 
184 | 현재 Cluster 설정을 읽는 정확한 위치와 명령은 Kubespray Runbook·검증 기준을 따른다.
185 | 
186 | 대표적으로 kubeadm 관련 ConfigMap 등을 조회할 수 있다.
187 | 
188 | ```bash
189 | kubectl -n kube-system get cm kubeadm-config -o yaml
190 | ```
191 | 
192 | > 출력 전체를 외우는 것이 아니라 **어제 기대값과 오늘 실제값을 한 항목씩 대조**합니다.
193 | 
194 | ## 4.1 반드시 구분할 것
195 | 
196 | ```text
197 | 설정 객체 존재
198 | ≠ 값이 승인 설계와 일치
199 | 
200 | Kubernetes Version 출력
201 | ≠ Bundle·Registry·Package 기준까지 모두 일치
202 | ```
203 | 
204 | 값이 다르면 “설치가 됐으니 나중에 고친다”로 넘기지 않는다. 영향이 큰 Cluster Identity·Network 값은 다음 기능 검증 전에 원인과 범위를 판정한다.
205 | 
206 | ---
207 | 
208 | # 5. Node — 목록이 아니라 예상 설계와 실제 등록을 대조한다
209 | 
210 | 대표 조회:
211 | 
212 | ```bash
213 | kubectl get nodes -o wide
214 | ```
215 | 
216 | 한 Node에서 볼 핵심은 다음 정도다.
217 | 
218 | ```text
219 | NAME
220 | STATUS
221 | ROLES 또는 Label 기반 Role
222 | INTERNAL-IP
223 | VERSION
224 | OS
225 | CONTAINER-RUNTIME
226 | ```
227 | 
228 | ## 5.1 Node 목록 표시와 정상 등록을 분리한다
229 | 
230 | ```text
231 | Node 이름이 목록에 있음
232 | ≠ 기대한 VM이 맞음
233 | 
234 | 모든 Node가 표시됨
235 | ≠ Role이 올바름
236 | 
237 | Ready
238 | ≠ Version·IP·Runtime·Label·Taint가 승인 설계와 일치
239 | ```
240 | 
241 | 따라서 각 Node를 8월 31일 기대표와 대조한다.
242 | 
243 | ```text
244 | 기대 Hostname
245 | ↔ 실제 NAME
246 | 
247 | 기대 Management/Internal IP
248 | ↔ 실제 INTERNAL-IP
249 | 
250 | 기대 Role
251 | ↔ 실제 Label·Role
252 | 
253 | 기대 Kubernetes Version
254 | ↔ 실제 VERSION
255 | ```
256 | 
257 | ## 5.2 Node Ready가 증명하는 범위
258 | 
259 | ```text
260 | Ready=True
261 | → kubelet이 Control Plane과 기본 상태 보고를 주고받는 경로가 성립
262 | ```
263 | 
264 | 하지만:
265 | 
266 | ```text
267 | Ready=True
268 | ≠ 실제 Pod Network 통신 정상
269 | ≠ Cluster DNS 질의 정상
270 | ≠ Ingress 사용자 경로 정상
271 | ≠ Storage 정상
272 | ```
273 | 
274 | > 이 경계가 다음 블록이 필요한 이유입니다.
275 | 
276 | ---
277 | 
278 | # 6. Label과 Taint는 Role 이름보다 실제 배치 정책을 만든다
279 | 
280 | > Master·Router·Infra·Worker 같은 Role은 표시용 이름만이 아니라 뒤 Workload 배치에 영향을 줍니다.
281 | 
282 | 확인 질문:
283 | 
284 | ```text
285 | Master는 Control Plane 역할 Label·Taint가 기대대로 있는가
286 | Router는 Ingress 배치 대상 Label·Taint가 있는가
287 | Infra는 플랫폼 Workload 배치 조건이 있는가
288 | Worker는 사용자 Workload 조건과 맞는가
289 | ETCD는 승인 설계의 Role 경계가 유지되는가
290 | ```
291 | 
292 | 정확한 Label·Taint 값은 현재 Bundle과 8월 31일 승인 설계를 따른다.
293 | 
294 | 구분:
295 | 
296 | ```text
297 | Role 문자열 표시
298 | ≠ 필요한 Label·Taint 정책 전체 정상
299 | ```
300 | 
301 | > 다음 날 Monitoring·KubeSphere는 Infra 배치 조건을 실제로 사용하므로 지금 잘못된 Role·Label을 “Pod가 뜨면 된다”로 넘기지 않습니다.
302 | 
303 | ---
304 | 
305 | # 7. Control Plane은 세 역할을 각각 본다
306 | 
307 | Kubernetes Control Plane의 핵심 역할:
308 | 
309 | ```text
310 | kube-apiserver
311 | → 모든 Kubernetes API 요청의 입구
312 | 
313 | kube-controller-manager
314 | → 원하는 상태와 실제 상태를 맞추는 Controller 실행
315 | 
316 | kube-scheduler
317 | → 새 Pod를 어느 Node에 배치할지 결정
318 | ```
319 | 
320 | 설치 방식에 따라 Static Pod 등으로 확인할 수 있다. 정확한 조회는 현재 Cluster 구조를 따른다.
321 | 
322 | 대표 조회:
323 | 
324 | ```bash
325 | kubectl -n kube-system get pods -o wide
326 | ```
327 | 
328 | 또는 필요한 Label/이름으로 좁혀 본다.
329 | 
330 | ## 7.1 Pod Running과 기능 정상은 다르다
331 | 
332 | ```text
333 | Control Plane Pod Running
334 | ≠ Restart·Event·Endpoint까지 정상
335 | ```
336 | 
337 | 확인할 최소 항목:
338 | 
339 | ```text
340 | 예상 Replica 또는 Node별 배치
341 | Ready 상태
342 | Restart 급증 없음
343 | 실제 NODE가 기대 Master인지
344 | Critical Event 없음
345 | ```
346 | 
347 | > Pod 이름 suffix는 외우지 않습니다. **어떤 역할 Component가 어느 Master에서 왜 있어야 하는지**를 이해합니다.
348 | 
349 | ---
350 | 
351 | # 8. kube-proxy와 System Pod를 전체 성공으로 확대하지 않는다
352 | 
353 | > `kube-system`에 Pod가 많이 Running이면 좋아 보이지만 하나의 총점으로 판정하지 않습니다.
354 | 
355 | 예:
356 | 
357 | ```text
358 | kube-proxy
359 | → Node의 Service Network 처리 일부
360 | 
361 | CoreDNS
362 | → Cluster DNS
363 | 
364 | Calico
365 | → Pod Network
366 | ```
367 | 
368 | 이 블록에서는 kube-proxy와 전체 System Pod에 명백한 이상이 없는지 확인하지만, **CoreDNS와 Calico의 실제 기능 성공은 다음 블록에서 별도 검증**한다.
369 | 
370 | 구분:
371 | 
372 | ```text
373 | System Pod Running
374 | ≠ Data Plane 실제 기능 정상
375 | ```
376 | 
377 | ---
378 | 
379 | # 9. 비정상이면 같은 대상에서 첫 차이를 찾는다
380 | 
381 | 대표 분기:
382 | 
383 | | 증상 | 첫 확인 |
384 | |---|---|
385 | | `kubectl` 연결 실패 | kubeconfig Context·Server URL·VIP-A·TLS·Network |
386 | | Master 직접 API는 되나 VIP-A 실패 | LB Frontend·Backend·TLS/API 경로 |
387 | | 기대 Node 누락 | Inventory·kubelet·Network·Join/Bootstrap 상태 |
388 | | 한 Node NotReady | 해당 Node Condition·kubelet·Network·Runtime 차이 |
389 | | Role·IP 다름 | 8/31 Inventory와 실제 Node Identity 대조 |
390 | | Control Plane Pod 비정상 | 해당 Master·Pod Event·Static Pod/Service 상태 |
391 | | Version 불일치 | Bundle·Inventory·Package·설치 로그 |
392 | 
393 | > 전체 Cluster 재설치로 바로 가지 않습니다. **정상 Node와 실패 Node의 첫 차이**를 먼저 찾습니다.
394 | 
395 | ---
396 | 
397 | # 10. Control Path PASS를 판정한다
398 | 
399 | 이 블록의 완료 기준:
400 | 
401 | ```text
402 | 신규 Member kubeconfig·Context 확인
403 | + API Server가 승인 VIP-A를 가리킴
404 | + API readiness 정상
405 | + 8/31 VIP·CIDR·Domain·Version 기대값과 실제 설정 대조
406 | + 예상 Node가 모두 등록
407 | + Node Name·IP·Role·Version 일치
408 | + 필요한 Node Ready
409 | + Role별 Label·Taint가 승인 설계와 일치
410 | + Control Plane 핵심 Component 정상
411 | + 미해결 Critical Event 없음
412 | ```
413 | 
414 | 이를 다음과 같이 부른다.
415 | 
416 | ```text
417 | CONTROL PATH PASS
418 | ```
419 | 
420 | 하지만 아직:
421 | 
422 | ```text
423 | External ETCD 상태
424 | 실제 Container 실행
425 | Pod Network
426 | 실제 DNS 질의
427 | Ingress·VIP-B 사용자 경로
428 | ```
429 | 
430 | 를 닫지 않았다.
431 | 
432 | ---
433 | 
434 | # 11. BLOCKED 기준
435 | 
436 | 다음 중 하나가 미해결이면 다음 Data Plane 검증의 정상 PASS 흐름으로 넘기지 않는다.
437 | 
438 | ```text
439 | 대상 Context 불명확
440 | VIP-A API 경로 비정상
441 | 전역 Cluster Identity·CIDR·Domain 불일치
442 | 예상 Node 누락
443 | Node Identity·Role·Version 중대한 불일치
444 | 필수 Node NotReady 원인 미확정
445 | Control Plane 핵심 Component 비정상
446 | Critical Event 미해결
447 | ```
448 | 
449 | > BLOCKED라면 어디까지 성공했고 어느 증거에서 처음 달라졌는지 남깁니다.
450 | 
451 | ---
452 | 
453 | # 12. 다음 ETCD·Runtime·CNI·DNS·Ingress 블록으로 넘길 것
454 | 
455 | ```text
456 | Cluster Name·Stage
457 | current-context·API Server URL
458 | VIP-A 검증 결과
459 | 실제 Kubernetes Version
460 | 실제 Pod CIDR·Service CIDR·Domain
461 | Node별 Name·Role·IP·Version·Ready
462 | Role별 Label·Taint 확인 결과
463 | Control Plane Component 상태
464 | Critical Event·미해결 항목
465 | CONTROL PATH PASS / BLOCKED 판정
466 | ```
467 | 
468 | > 다음 블록에서는 같은 Context에서 **Application Pod가 실제로 실행되고 통신하고 이름을 찾으며 외부 요청을 받을 수 있는지** 검증합니다.
469 | 
470 | ---
471 | 
472 | # 13. 마무리 — Control Path를 한 문장으로 다시 말한다
473 | 
474 | > 오전 Playbook 성공은 자동화 단계가 끝났다는 뜻이었습니다.
475 | >
476 | > 오후 첫 검증에서는 그 입력이 실제 신규 Member Kubernetes로 만들어졌는지 확인합니다. 먼저 Context와 VIP-A API를 고정하고, 8월 31일의 전역 설계값이 실제 Cluster에 반영됐는지 대조합니다.
477 | >
478 | > 그다음 예상 Node가 올바른 Name·IP·Role·Version으로 등록되고 Ready인지, Control Plane 핵심 Component가 정상인지 확인합니다.
479 | >
480 | > **결국 `kubectl get nodes`가 보기 좋다는 것이 아니라, 우리가 만들기로 한 신규 Member의 Control Path가 실제로 같은 Identity와 설계로 성립했다는 것이 이 블록의 성공입니다.**
481 | 
482 | ---
483 | 
484 | # 14. 마지막 Teach-back
485 | 
486 | 1. `kubectl` 결과를 보기 전에 kubeconfig와 Context를 먼저 확인해야 하는 이유는 무엇인가?
487 | 2. Master 직접 API 성공과 VIP-A API 성공은 왜 다른 증거인가?
488 | 3. 8월 31일의 CIDR·Domain·Version 기대값을 설치 후 다시 확인하는 이유는 무엇인가?
489 | 4. Node가 목록에 보이는 것과 올바른 Role·IP로 등록된 것은 무엇이 다른가?
490 | 5. Node Ready는 무엇을 증명하고 CNI·DNS·Ingress에 대해서는 무엇을 증명하지 못하는가?
491 | 6. Role 문자열뿐 아니라 Label·Taint를 확인해야 하는 이유는 무엇인가?
492 | 7. Control Plane Pod Running과 Control Path PASS는 무엇이 다른가?
493 | 8. 다음 블록으로 넘길 최소 증거는 무엇인가?
494 | 
495 | ---
496 | 
497 | # 기준 문서 바로가기
498 | 
499 | - [[출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증|2026-09-01 Member 구축 2일차 기준]]
500 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
501 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
502 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-01/오후/02. External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본.md

Bytes: 18416
SHA-256: 5e7f325e96813cc1aab5287a09aa8f0651564f5fae51791eca7e8f1f3aacd475
Lines: 1-617 of 617

```markdown
  1 | ---
  2 | title: "External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-01 Xi'an 신규 Member 구축 2일차 오후 - ETCD·Runtime·Pod Network·DNS·Ingress 실제 기능과 9월 2일 Storage Gate"
  6 | created: "2026-08-27"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 앞 블록의 `CONTROL PATH PASS` 뒤에 **실제 Application Pod가 실행되고, Pod Network와 Cluster DNS를 사용하며, 외부 요청이 VIP-B에서 Service·Pod까지 이어질 수 있는지 증명하는 법**을 가르친다. ETCD·containerd·Calico·CoreDNS·Ingress의 긴 설정을 외우게 하지 않는다. 설정 존재와 실제 기능 성공을 분리하고, 9월 2일 Storage를 시작할 Kubernetes 기반이 있는지 `KUBERNETES BASE PASS / BLOCKED`로 판정한다.
 14 | 
 15 | ## 0. 앞 블록에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage
 19 | current-context·API Server URL
 20 | VIP-A 검증 결과
 21 | 실제 Kubernetes Version
 22 | 실제 Pod CIDR·Service CIDR·Domain
 23 | Node별 Name·Role·IP·Version·Ready
 24 | Role별 Label·Taint
 25 | Control Plane Component 상태
 26 | CONTROL PATH PASS / BLOCKED
 27 | ```
 28 | 
 29 | > 이 값은 다시 추측하지 않습니다. 같은 Context를 유지한 채 Control Path 뒤의 실제 Application 경로를 검증합니다.
 30 | 
 31 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 32 | 
 33 | > ETCD·containerd·Calico·CoreDNS·Ingress Pod가 Running이라는 사실만으로 완료 처리하지 않고, **상태 저장 → Container 실행 → Pod IP·통신 → Service 이름 해석 → Service Endpoint → Router NodePort → VIP-B 사용자 요청**의 실제 기능 경로를 단계별 증거로 확인할 수 있어야 한다.
 34 | 
 35 | 오늘의 중심 질문:
 36 | 
 37 | > **이 Cluster에서 실제 Pod를 실행하고 Network와 DNS를 사용하며 외부 요청을 Application까지 전달할 수 있는가?**
 38 | 
 39 | ---
 40 | 
 41 | # 1. 시작 — Node Ready 뒤에도 Application이 동작한다는 증거는 남아 있다
 42 | 
 43 | > 앞 블록에서는 API Server가 응답하고 예상 Node가 올바른 Identity로 등록되며 Control Plane 핵심 Component가 정상임을 확인했습니다.
 44 | >
 45 | > 이제 `그럼 Application Pod를 하나 만들면 실제로 실행되고 통신하며 사용자가 접근할 수 있는가?`를 묻습니다.
 46 | >
 47 | > 아직 바로 예라고 할 수 없습니다.
 48 | 
 49 | Application 경로에 필요한 역할을 최소 다섯 가지로 본다.
 50 | 
 51 | ```text
 52 | Cluster 상태를 보존
 53 | → External ETCD
 54 | 
 55 | Image로 Container를 실행
 56 | → CRI·containerd
 57 | 
 58 | Pod에 IP와 통신 경로 제공
 59 | → CNI·Calico
 60 | 
 61 | Service 이름을 IP로 해석
 62 | → CoreDNS
 63 | 
 64 | 외부 HTTP·HTTPS 요청을 Service로 전달
 65 | → Ingress Controller·Router·VIP-B
 66 | ```
 67 | 
 68 | > 이 역할들은 연결되지만 하나의 성공이 뒤의 성공을 대신하지 않습니다.
 69 | 
 70 | ---
 71 | 
 72 | # 2. 같은 신규 Member Context와 기능 테스트 범위를 고정한다
 73 | 
 74 | ```text
 75 | current-context: _________________________________________
 76 | Cluster Name·Stage: _____________________________________
 77 | Pod CIDR: ________________________________________________
 78 | Service CIDR·Domain: _____________________________________
 79 | VIP-B·80/443: ____________________________________________
 80 | Router Role Node: ________________________________________
 81 | Registry FQDN·Project: ___________________________________
 82 | External ETCD Endpoint 기준: _____________________________
 83 | 검증 시작 시각: _________________________________________
 84 | ```
 85 | 
 86 | > 다른 Cluster의 ETCD나 Registry가 정상이어도 오늘 신규 Member의 증거가 아닙니다.
 87 | 
 88 | 기능 검증에서 사용할 임시 Resource는 승인된 Runbook의 Test Manifest를 사용한다.
 89 | 
 90 | 원칙:
 91 | 
 92 | ```text
 93 | 고유한 Test 이름
 94 | 승인된 Namespace
 95 | 승인된 Image
 96 | 변경 영향 최소
 97 | 정리 계획 선확정
 98 | 민감정보 없음
 99 | ```
100 | 
101 | > 긴 Test Manifest는 이 대본에 복제하지 않습니다. 무엇을 증명하기 위해 만드는지만 기억합니다.
102 | 
103 | ---
104 | 
105 | # 3. External ETCD — 상태 저장소가 같은 신규 Member를 보존하는가
106 | 
107 | > External ETCD는 Kubernetes API가 보존해야 할 Cluster 상태를 저장합니다. Kubernetes Pod 목록에 ETCD Pod가 보이지 않아도 External Node에서 별도로 실행될 수 있습니다.
108 | 
109 | 반드시 구분한다.
110 | 
111 | ```text
112 | kube-system에 ETCD Pod 없음
113 | ≠ ETCD 없음
114 | 
115 | ETCD Process 실행
116 | ≠ Member 전체 정상
117 | 
118 | Member 목록 정상
119 | ≠ 모든 Endpoint 상태 정상
120 | ```
121 | 
122 | ## 3.1 확인할 최소 질문
123 | 
124 | ```text
125 | 현재 신규 Member의 ETCD Endpoint인가
126 | 기대 Member 수가 있는가
127 | 각 Endpoint가 건강한가
128 | Leader가 존재하는가
129 | Cluster ID가 하나로 연결되는가
130 | ```
131 | 
132 | 정확한 `etcdctl` 인증서·Endpoint 옵션은 현재 승인 Runbook을 따른다. Certificate·Private Key 원문은 화면과 증적에 복사하지 않는다.
133 | 
134 | ## 3.2 ETCD가 증명하는 범위
135 | 
136 | ETCD health가 정상이라면:
137 | 
138 | ```text
139 | Kubernetes 상태 저장 경로의 기본 기능이 성립
140 | ```
141 | 
142 | 하지만:
143 | 
144 | ```text
145 | ETCD 정상
146 | ≠ Node Container 실행 정상
147 | ≠ Pod Network 정상
148 | ≠ DNS·Ingress 정상
149 | ```
150 | 
151 | > ETCD가 비정상이면 뒤 기능 테스트를 계속해 원인을 복잡하게 만들지 않습니다.
152 | 
153 | ---
154 | 
155 | # 4. Runtime — Service가 떠 있는 것과 실제 Container 실행을 분리한다
156 | 
157 | > Kubernetes가 Pod를 실행하려면 각 Node의 kubelet이 Container Runtime에 Container 생성을 요청합니다. 이 환경에서는 containerd가 그 역할을 담당합니다.
158 | 
159 | 구분:
160 | 
161 | ```text
162 | containerd Service Running
163 | ≠ Kubernetes가 실제 Container 생성 성공
164 | 
165 | containerd Version 출력
166 | ≠ 승인 Version·Config 정상
167 | 
168 | Registry 설정 파일 존재
169 | ≠ 실제 Private Image Pull 성공
170 | ```
171 | 
172 | 확인할 최소 범위:
173 | 
174 | ```text
175 | 대상 Node의 containerd Service 상태
176 | Runtime Version
177 | Kubernetes가 보고한 CONTAINER-RUNTIME
178 | 필요한 Registry Trust·Endpoint 기준
179 | 실제 Test Pod의 Container Created·Started
180 | ```
181 | 
182 | > Registry Image Pull에 실패하면 Runtime 자체를 재설치하기 전에 Pod Event의 실제 Image 주소, DNS·Network·CA·Credential·Tag 중 처음 끊긴 지점을 봅니다.
183 | 
184 | ---
185 | 
186 | # 5. Calico — DaemonSet Running보다 실제 Pod Network가 중요하다
187 | 
188 | > CNI는 Pod가 Network를 사용할 수 있게 연결하는 표준 경계이고, 현재 환경에서는 Calico가 이 역할을 수행합니다.
189 | 
190 | 확인할 개념:
191 | 
192 | ```text
193 | calico-node
194 | → 각 대상 Kubernetes Node의 Network Agent
195 | 
196 | Calico Controller
197 | → Network 상태·정책 관련 Control 기능
198 | 
199 | IPPool·Backend
200 | → Pod IP 대역과 Network 동작 기준
201 | ```
202 | 
203 | 반드시 구분한다.
204 | 
205 | ```text
206 | calico-node Running
207 | ≠ 실제 Pod IP 할당·통신 정상
208 | 
209 | IPPool 객체 존재
210 | ≠ 승인 Pod CIDR와 일치
211 | ```
212 | 
213 | ## 5.1 설정과 실제 설계를 대조한다
214 | 
215 | ```text
216 | 8/31 승인 Pod CIDR
217 | ↔ 실제 Cluster Pod CIDR
218 | ↔ Calico IPPool
219 | ```
220 | 
221 | Role별 대상 Node에 필요한 Calico Agent가 존재하는지도 확인한다.
222 | 
223 | > ETCD 전용 VM처럼 Kubernetes Node가 아닌 Server를 DaemonSet 대상 수에 포함하지 않습니다.
224 | 
225 | ---
226 | 
227 | # 6. Test Pod — Runtime과 CNI를 실제로 통과한다
228 | 
229 | > 이제 설정 객체를 보는 데서 멈추지 않고 승인된 임시 Pod를 실제로 실행합니다.
230 | 
231 | Test Pod가 답해야 할 질문:
232 | 
233 | ```text
234 | Scheduler가 Node를 선택했는가
235 | Image Pull이 성공했는가
236 | Container가 Created·Started됐는가
237 | Pod가 Ready·Running인가
238 | Pod IP가 승인 Pod CIDR에서 할당됐는가
239 | 실제 NODE가 기대 역할인가
240 | ```
241 | 
242 | 대표 조회:
243 | 
244 | ```bash
245 | kubectl get pod -n <test-namespace> <test-pod> -o wide
246 | kubectl describe pod -n <test-namespace> <test-pod>
247 | ```
248 | 
249 | 증거 범위:
250 | 
251 | ```text
252 | Pod Running + Pod IP
253 | → Scheduler·Runtime·CNI의 중요한 실제 경로가 통과
254 | ```
255 | 
256 | 하지만:
257 | 
258 | ```text
259 | Pod Running
260 | ≠ Cluster DNS 질의 성공
261 | ≠ 외부 Ingress 성공
262 | ```
263 | 
264 | ## 6.1 실패 분기
265 | 
266 | | 상태·Event | 첫 확인 |
267 | |---|---|
268 | | Pending / Unschedulable | Node Label·Taint·Resource·Scheduler Event |
269 | | ImagePullBackOff | Image 주소·Registry·CA·Credential·Network |
270 | | ContainerCreating 장기 지속 | CNI·Mount·Runtime Event |
271 | | CrashLoopBackOff | Container Log·Command·Application 상태 |
272 | | Pod IP 없음 | CNI·Calico Node·IPPool·Node Network |
273 | 
274 | > 상태 이름을 원인으로 외우지 않고 Event의 실제 문장을 읽습니다.
275 | 
276 | ---
277 | 
278 | # 7. Service와 Endpoint — Pod가 있다고 Service 경로가 자동으로 생기지 않는다
279 | 
280 | > Application을 안정적으로 찾기 위해 Kubernetes는 Pod 앞에 Service를 둡니다.
281 | 
282 | 기본 경로:
283 | 
284 | ```text
285 | Service
286 | → Selector
287 | → Endpoint 또는 EndpointSlice
288 | → 실제 Pod IP:Port
289 | ```
290 | 
291 | 확인할 질문:
292 | 
293 | ```text
294 | Service가 의도한 Selector를 갖는가
295 | Endpoint가 실제 Test Pod를 가리키는가
296 | Port와 TargetPort가 맞는가
297 | ```
298 | 
299 | 구분:
300 | 
301 | ```text
302 | Service 존재
303 | ≠ Endpoint 존재
304 | 
305 | Endpoint 존재
306 | ≠ 실제 요청 성공
307 | ```
308 | 
309 | > 이후 DNS와 Ingress가 이 Service를 사용하므로 Service·Endpoint가 잘못된 상태에서 CoreDNS나 VIP-B부터 조사하지 않습니다.
310 | 
311 | ---
312 | 
313 | # 8. CoreDNS — Pod Running과 실제 이름 해석을 구분한다
314 | 
315 | > CoreDNS는 Cluster 안에서 Service 이름을 ClusterIP로 찾게 합니다.
316 | 
317 | 정상 경로:
318 | 
319 | ```text
320 | Test Pod
321 | → Service DNS 이름 질의
322 | → CoreDNS
323 | → Service ClusterIP 반환
324 | → Service Endpoint 접근
325 | ```
326 | 
327 | 구분:
328 | 
329 | ```text
330 | CoreDNS Pod Running
331 | ≠ 실제 DNS Query 성공
332 | 
333 | DNS Query 성공
334 | ≠ 대상 Service Endpoint 기능 성공
335 | ```
336 | 
337 | ## 8.1 실제 질의
338 | 
339 | 승인된 Test Pod에서 현재 Service 이름을 조회한다.
340 | 
341 | 예:
342 | 
343 | ```bash
344 | kubectl exec -n <test-namespace> <test-pod> -- \
345 |   getent hosts <test-service>.<test-namespace>.svc.<current-domain>
346 | ```
347 | 
348 | 현재 Image에 `getent`가 없다면 Runbook이 지정한 승인된 DNS Test 도구를 사용한다.
349 | 
350 | 검증:
351 | 
352 | ```text
353 | 질의 이름이 현재 Cluster Domain 사용
354 | + 반환 ClusterIP가 실제 Service와 일치
355 | + 실제 Service 요청도 성공
356 | ```
357 | 
358 | > 과거 Cluster Domain으로 우연히 질의가 성공하거나 `/etc/hosts`로 우회된 결과를 Cluster DNS 증거로 사용하지 않습니다.
359 | 
360 | ---
361 | 
362 | # 9. Ingress — Controller Running 뒤의 사용자 경로를 실제로 연결한다
363 | 
364 | > 외부 사용자가 Application에 접근할 때는 Router Role의 Ingress Controller와 VIP-B가 이어집니다.
365 | 
366 | 전체 경로:
367 | 
368 | ```text
369 | 사용자 또는 Test Source
370 | → DNS / FQDN
371 | → VIP-B:80 또는 443
372 | → Router Backend
373 | → ingress-nginx-controller
374 | → Ingress Rule
375 | → Service
376 | → Endpoint
377 | → Pod
378 | ```
379 | 
380 | ## 9.1 먼저 Controller 배치를 본다
381 | 
382 | ```text
383 | Ingress Controller Pod Ready
384 | + 실제 NODE가 승인 Router
385 | + 필요한 Label·Taint·Toleration 일치
386 | ```
387 | 
388 | 구분:
389 | 
390 | ```text
391 | Ingress Controller Running
392 | ≠ Ingress Rule 정상
393 | ≠ Service Endpoint 정상
394 | ≠ VIP-B Mapping 정상
395 | ```
396 | 
397 | ## 9.2 Router NodePort와 VIP-B를 분리한다
398 | 
399 | Xi'an 설계의 대표 구조는 현재 승인값을 확인해 다음 관계로 읽는다.
400 | 
401 | ```text
402 | VIP-B:80
403 | → Router의 승인 HTTP NodePort
404 | 
405 | VIP-B:443
406 | → Router의 승인 HTTPS NodePort
407 | ```
408 | 
409 | > 정확한 NodePort는 현재 Service 출력과 승인 설계를 사용합니다. 과거 `30080`, `30443` 값을 자동으로 현재값으로 사용하지 않습니다.
410 | 
411 | 먼저 Router 경로를 확인하고 그다음 VIP-B를 본다.
412 | 
413 | ```text
414 | Service·Endpoint 정상
415 | → Router NodePort 응답
416 | → VIP-B Frontend 응답
417 | ```
418 | 
419 | 이 순서가 중요한 이유는 VIP-B 실패 시 Cluster 내부와 LB 경계를 분리할 수 있기 때문이다.
420 | 
421 | ---
422 | 
423 | # 10. HTTP 성공과 HTTPS 성공을 분리한다
424 | 
425 | ```text
426 | VIP-B HTTP 80 성공
427 | ≠ HTTPS 443 성공
428 | ```
429 | 
430 | HTTPS에는 추가로 다음이 들어갈 수 있다.
431 | 
432 | ```text
433 | Certificate
434 | TLS 종료 위치
435 | SNI·Host
436 | Ingress TLS 설정
437 | LB 방식
438 | ```
439 | 
440 | > `curl -k`로 응답이 나온다고 Certificate Trust까지 통과한 것은 아닙니다. 검증 목적을 명시하고 승인된 CA를 사용한 정상 TLS 확인을 별도로 판정합니다.
441 | 
442 | 9월 2일 Storage 진입 Gate에서 반드시 외부 Application HTTPS까지 요구하는지는 현재 일정·검증 기준을 따른다. 하지만 Router·Ingress 기본 경로의 미해결 오류는 Storage 이후로 미루지 않는다.
443 | 
444 | ---
445 | 
446 | # 11. Add-on은 전부 같은 중요도로 보지 않는다
447 | 
448 | > Kubespray Bundle에는 metrics-server 등 여러 Add-on이 있을 수 있습니다. 모든 Pod를 같은 중요도로 취급하면 핵심 Kubernetes 기반과 부가 기능을 구분하기 어렵습니다.
449 | 
450 | 우선순위:
451 | 
452 | ```text
453 | 9/2 Storage를 가능하게 하는 Kubernetes 핵심 기반
454 | → 반드시 PASS 필요
455 | 
456 | 부가 Add-on
457 | → 현재 일정상 다음 단계 필수인지 판단
458 | ```
459 | 
460 | 다만 다음은 비차단이라고 임의 판단하지 않는다.
461 | 
462 | ```text
463 | CNI
464 | CoreDNS
465 | API·Node 기반
466 | Container Runtime
467 | Storage가 의존하는 Node Network·DNS
468 | ```
469 | 
470 | > 다음 단계 선행조건을 실제로 바꾸는 기능은 반드시 닫습니다.
471 | 
472 | ---
473 | 
474 | # 12. 임시 Resource 정리도 검증의 일부다
475 | 
476 | > Test Pod·Service·Ingress를 만들었다면 성공 화면을 확인한 뒤 그대로 두지 않습니다.
477 | 
478 | 정리 전에 기록할 것:
479 | 
480 | ```text
481 | Test Namespace·Resource 이름
482 | 생성 목적
483 | 성공 증거
484 | 문제 조사에 더 필요한지
485 | 삭제 영향
486 | ```
487 | 
488 | 승인된 Runbook에 따라 Test Resource를 정리하고 다음을 확인한다.
489 | 
490 | ```text
491 | Test Pod·Service·Ingress 제거
492 | + 의도하지 않은 운영 Resource 영향 없음
493 | + 잔여 Endpoint 없음
494 | + Critical Event 없음
495 | ```
496 | 
497 | > 정리 결과를 확인하지 않은 실습은 완료가 아닙니다.
498 | 
499 | ---
500 | 
501 | # 13. 실패 시 전체 경로에서 첫 단절을 고른다
502 | 
503 | | 증상 | 먼저 볼 경계 |
504 | |---|---|
505 | | ETCD endpoint unhealthy | 실제 Endpoint·TLS·Network·Member 상태 |
506 | | Test Pod ImagePullBackOff | Image 주소·Registry·CA·Credential·Network |
507 | | Pod IP 없음 | Calico Agent·IPPool·Node Network |
508 | | Pod Running, DNS 실패 | CoreDNS·Service·Cluster Domain·Network |
509 | | DNS 성공, Service 요청 실패 | Service Selector·Endpoint·TargetPort |
510 | | Router NodePort 성공, VIP-B 실패 | LB Frontend·Backend·Health·Network |
511 | | VIP-B HTTP 성공, HTTPS 실패 | TLS·Certificate·443 Mapping·Ingress 설정 |
512 | 
513 | > 뒤 단계가 실패했다고 앞 단계까지 모두 실패로 되돌리지 않습니다. 마지막 성공과 첫 실패 사이를 좁힙니다.
514 | 
515 | ---
516 | 
517 | # 14. 9월 2일 Storage 진입 Gate
518 | 
519 | 9월 1일 종료 판정은 `KUBERNETES BASE PASS / BLOCKED` 두 상태만 사용한다.
520 | 
521 | ## 14.1 KUBERNETES BASE PASS
522 | 
523 | ```text
524 | CONTROL PATH PASS
525 | + External ETCD 기본 health·member 상태 정상
526 | + 각 Kubernetes Node의 Runtime 기본 상태 정상
527 | + 승인 Test Pod 실제 Container 실행
528 | + Calico 기반 Pod IP 할당·Network 기본 기능 정상
529 | + Service·Endpoint 정상
530 | + 실제 Cluster DNS 질의 성공
531 | + Ingress Controller가 승인 Router에 배치
532 | + Router NodePort 기본 경로 정상
533 | + 다음 단계에 필요한 VIP-B 경로 정상
534 | + 미해결 Critical Event 없음
535 | + Test Resource 정리 완료
536 | ```
537 | 
538 | > 이 상태는 Kubernetes 기반이 Storage Component를 설치하고 PVC·Pod를 검증할 만큼 성립했다는 뜻입니다.
539 | 
540 | ## 14.2 BLOCKED
541 | 
542 | 다음 중 Storage의 선행조건을 흔드는 문제가 남으면 BLOCKED다.
543 | 
544 | ```text
545 | External ETCD 비정상 원인 미확정
546 | 필수 Node Runtime 비정상
547 | Test Pod 실행 실패
548 | CNI·Pod IP·기본 통신 실패
549 | Cluster DNS 실제 질의 실패
550 | Service·Endpoint 기본 경로 실패
551 | Router·Ingress 기본 기능 실패
552 | Storage가 사용할 Node Network 경로의 중대한 이상
553 | Critical Event 미해결
554 | Test Resource 정리 위험 또는 영향 미확정
555 | ```
556 | 
557 | > Storage 설치가 의존하는 Kubernetes 기반이 미해결이면 다음 날짜로 넘기지 않고 먼저 닫습니다.
558 | 
559 | ---
560 | 
561 | # 15. 9월 2일로 넘길 증거
562 | 
563 | ```text
564 | Cluster Name·Stage·Context
565 | KUBERNETES BASE PASS / BLOCKED
566 | External ETCD member·health 결과
567 | Node별 Runtime 기준
568 | Pod CIDR·Calico 기준과 Test Pod IP
569 | Test Pod Scheduling·Created·Started 결과
570 | Service·Endpoint 결과
571 | CoreDNS 실제 질의 결과
572 | Ingress Controller 실제 Router 배치
573 | Router NodePort·VIP-B 결과
574 | 미해결 Event·외부 확인 항목
575 | Test Resource Cleanup 결과
576 | Storage 작업에서 사용할 Node Role·Network 전제
577 | ```
578 | 
579 | > Storage 대본에서는 이 Kubernetes 기반을 다시 전부 검증하지 않고 Gate 결과를 입력으로 사용합니다.
580 | 
581 | ---
582 | 
583 | # 16. 마무리 — 9월 1일의 전체 의미
584 | 
585 | > 8월 31일에는 현실을 확인하고 자동화 입력을 만들었습니다.
586 | >
587 | > 오늘 오전에는 그 입력으로 Kubespray를 실행하고 자동화 실패를 닫았습니다.
588 | >
589 | > 오후 첫 블록에서는 API·전역 설계·Node·Control Plane이라는 Control Path를 증명했습니다.
590 | >
591 | > 마지막으로 External ETCD, Runtime, CNI, DNS와 Ingress를 실제 Test Pod·Service·요청 경로로 확인했습니다.
592 | >
593 | > **결국 9월 1일 완료는 System Pod가 많이 Running인 상태가 아니라, 신규 Member가 상태를 보존하고 Container를 실행하며 Pod Network와 DNS를 사용하고 필요한 외부 요청 경로를 제공할 수 있다는 것을 독립 증거로 확인한 상태입니다.**
594 | 
595 | ---
596 | 
597 | # 17. 마지막 Teach-back
598 | 
599 | 1. ETCD Pod가 보이지 않는 것과 External ETCD가 없는 것은 왜 다른가?
600 | 2. containerd Service Running과 실제 Test Pod Container 실행은 왜 다른 증거인가?
601 | 3. calico-node Running 뒤에도 Test Pod IP와 Network를 확인해야 하는 이유는 무엇인가?
602 | 4. Service 존재와 Endpoint 존재, 실제 요청 성공은 어떻게 다른가?
603 | 5. CoreDNS Pod Running과 실제 Cluster DNS 질의 성공은 왜 다른가?
604 | 6. Router NodePort를 VIP-B보다 먼저 확인하면 어떤 실패 경계를 좁힐 수 있는가?
605 | 7. VIP-B HTTP 성공이 HTTPS 정상까지 증명하지 못하는 이유는 무엇인가?
606 | 8. Test Resource 정리 결과까지 확인해야 하는 이유는 무엇인가?
607 | 9. 어떤 조건이 남아 있으면 9월 2일 Storage로 넘어가면 안 되는가?
608 | 10. `KUBERNETES BASE PASS`가 증명하는 범위는 어디까지인가?
609 | 
610 | ---
611 | 
612 | # 기준 문서 바로가기
613 | 
614 | - [[출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증|2026-09-01 Member 구축 2일차 기준]]
615 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
616 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
617 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-02/오전/01. Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본.md

Bytes: 14300
SHA-256: 55c843fa30f60082bc321ad791afd0d1694fb1604465ace89d027cdffd55d2bd
Lines: 1-451 of 451

```markdown
  1 | ---
  2 | title: "Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-02 Xi'an 신규 Member 구축 3일차 오전 - Storage 공급 경로와 9월 2일 오후 사용 검증 선행조건"
  6 | created: "2026-08-28"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 9월 1일 `KUBERNETES BASE PASS`를 입력으로 받아 **Kubernetes의 PVC 요청이 실제 NetApp Storage 공급 경로까지 이어질 준비가 됐는지 판단하는 법**을 가르친다. Snapshotter·Trident·Backend·StorageClass의 정확한 설치 Manifest와 변경 명령은 Storage Runbook에서 수행한다. 여기서는 **구성요소가 존재하는 것과 공급 경로가 실제로 준비된 것을 구분하고, 오후 PVC·Mount·Write/Read 검증을 시작해도 되는지 판정하는 것**이 목적이다.
 14 | 
 15 | ## 0. 9월 1일에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage·Context
 19 | KUBERNETES BASE PASS / BLOCKED
 20 | API·Node·Control Plane 정상 증거
 21 | External ETCD 기본 상태
 22 | Node별 Runtime 기준
 23 | Pod CIDR·CNI·Cluster DNS 실제 기능
 24 | Ingress·VIP-B 기본 경로
 25 | Storage 작업에서 사용할 Node Role·Network 전제
 26 | 미해결 Event·외부 확인 항목
 27 | ```
 28 | 
 29 | > `BLOCKED`라면 Storage 설치를 시작하지 않습니다. Kubernetes 기반 문제 위에 Storage 오류를 겹치지 않습니다.
 30 | 
 31 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 32 | 
 33 | > Snapshotter, Trident Controller·Node Plugin, Backend와 StorageClass를 하나의 공급 경로로 설명하고, **각 구성요소의 존재가 어디까지를 증명하며 무엇은 아직 증명하지 못하는지** 구분해 오후 실제 사용 검증 진입 여부를 판단할 수 있어야 한다.
 34 | 
 35 | 오늘의 중심 질문:
 36 | 
 37 | > **Kubernetes가 PVC를 요청했을 때 승인된 Storage 정책과 실제 NetApp Backend를 통해 Volume을 공급할 준비가 됐는가?**
 38 | 
 39 | ---
 40 | 
 41 | # 1. 시작 — StorageClass가 보인다고 Storage가 준비된 것은 아니다
 42 | 
 43 | > 어제까지 Kubernetes 자체가 Pod를 실행하고 Network와 DNS를 사용하는 기반을 확인했습니다.
 44 | >
 45 | > 오늘은 Pod가 데이터를 저장할 공간을 요청했을 때 그 요청을 실제 Storage로 연결하는 경로를 만듭니다.
 46 | 
 47 | 전체 공급 경로를 먼저 본다.
 48 | 
 49 | ```text
 50 | Snapshot API·Controller
 51 | → CSI Snapshot 기능의 선행 API
 52 | 
 53 | Trident Operator·Controller
 54 | → Kubernetes PVC 요청을 NetApp Storage 작업으로 연결
 55 | 
 56 | Trident Node Plugin
 57 | → 각 Node에서 Volume Attach·Mount 경로에 참여
 58 | 
 59 | Backend
 60 | → Trident가 실제 NetApp SVM·Data LIF·정책과 연결되는 대상
 61 | 
 62 | StorageClass
 63 | → 사용자가 PVC에서 선택하는 Storage 공급 정책
 64 | ```
 65 | 
 66 | 그리고 오후에야 다음이 이어진다.
 67 | 
 68 | ```text
 69 | PVC
 70 | → PV
 71 | → Pod Mount
 72 | → Write·Read
 73 | ```
 74 | 
 75 | > 오전은 **Storage를 공급할 준비**를 닫는 시간이고, 오후는 **실제로 소비할 수 있는지**를 증명하는 시간입니다.
 76 | 
 77 | ---
 78 | 
 79 | # 2. 먼저 현재 Member와 Storage 실제값 Source를 고정한다
 80 | 
 81 | ```text
 82 | current-context: _________________________________________
 83 | Cluster Name·Stage: _____________________________________
 84 | KUBERNETES BASE PASS 증거: ______________________________
 85 | Storage 담당자·승인 근거: _______________________________
 86 | 승인 StorageClass 이름: _________________________________
 87 | 승인 Trident Version·Bundle: _____________________________
 88 | 승인 Backend Name: ______________________________________
 89 | 승인 SVM: ________________________________________________
 90 | 승인 Data LIF: ___________________________________________
 91 | 승인 Driver·Protocol: ____________________________________
 92 | 9/3 Monitoring 대상 Node Role: ___________________________
 93 | ```
 94 | 
 95 | > Credential·Password·Secret Data는 기록하지 않습니다. Backend 연결에 필요한 값은 승인된 관리체계와 Runbook에서 사용하고 교육 문서에는 구조와 판정만 남깁니다.
 96 | 
 97 | ## 2.1 과거 Xi'an 값은 구조 비교 자료다
 98 | 
 99 | ```text
100 | 기존 Backend 이름이 보임
101 | ≠ 신규 Member Backend
102 | 
103 | 기존 StorageClass가 동작함
104 | ≠ 신규 Member에서 승인된 정책
105 | ```
106 | 
107 | > 이름이 같더라도 승인 근거와 현재 Backend 연결을 다시 확인합니다.
108 | 
109 | ---
110 | 
111 | # 3. Snapshotter — Trident와 다른 선행 기능이다
112 | 
113 | > CSI Snapshotter는 Volume Snapshot API와 Controller 역할을 제공합니다. Trident와 함께 Storage 기능에서 사용될 수 있지만 같은 Component가 아닙니다.
114 | 
115 | 구분:
116 | 
117 | ```text
118 | Snapshot CRD 존재
119 | ≠ Snapshot Controller 정상
120 | 
121 | Controller Running
122 | ≠ Trident Backend 정상
123 | ```
124 | 
125 | 확인할 최소 질문:
126 | 
127 | ```text
128 | 현재 Bundle이 요구하는 Snapshot CRD가 있는가
129 | API에서 CRD가 Established 상태인가
130 | Controller가 승인 Namespace·Replica로 정상인가
131 | 반복 Restart·ImagePull·권한 오류가 없는가
132 | ```
133 | 
134 | 정확한 CRD·Controller 설치는 Storage Runbook을 따른다.
135 | 
136 | ## 3.1 CRD Apply 성공과 API 사용 가능을 분리한다
137 | 
138 | ```text
139 | kubectl apply 성공
140 | ≠ CRD Established
141 | ```
142 | 
143 | > `Established=True`까지 확인해야 Kubernetes API가 해당 Resource Kind를 안정적으로 사용할 준비가 됐다고 판단합니다.
144 | 
145 | ---
146 | 
147 | # 4. Trident — Controller와 Node 경로를 분리한다
148 | 
149 | > Trident는 Kubernetes CSI 요청과 NetApp Storage를 연결합니다. 하나의 Pod만 보는 것이 아니라 Controller 역할과 Node 역할을 구분해야 합니다.
150 | 
151 | ```text
152 | Operator
153 | → Trident 설치·구성 관리
154 | 
155 | Controller
156 | → Provisioning 등 Cluster 단위 Storage 작업
157 | 
158 | Node Plugin
159 | → Pod가 배치된 Node의 Mount 경로 참여
160 | ```
161 | 
162 | ## 4.1 Controller 정상과 전체 Node 정상은 다르다
163 | 
164 | ```text
165 | Trident Controller Running
166 | ≠ 모든 대상 Node Plugin 정상
167 | ```
168 | 
169 | 확인할 최소 범위:
170 | 
171 | ```text
172 | Operator 상태
173 | Controller Ready·Restart
174 | Node DaemonSet Desired·Ready·Available
175 | 대상 Kubernetes Node 누락 여부
176 | 9/3 Monitoring이 배치될 Infra Node에 Node Plugin 존재
177 | Critical Event 없음
178 | ```
179 | 
180 | > Worker에서만 Node Plugin이 정상이라고 9월 3일 Monitoring용 Infra Node Mount 경로까지 성공한 것으로 보지 않습니다.
181 | 
182 | ## 4.2 Image와 권한 실패는 Event에서 먼저 분리한다
183 | 
184 | | 증상 | 첫 확인 |
185 | |---|---|
186 | | ImagePullBackOff | Image 주소·Registry·Tag·CA·Secret |
187 | | Pending | Label·Taint·Resource·Scheduler Event |
188 | | CrashLoopBackOff | Container Log·Config·권한 |
189 | | 특정 Node Plugin 누락 | Node Selector·Taint·DaemonSet 대상 조건 |
190 | 
191 | > Storage 문제라는 큰 이름으로 묶기 전에 현재 Component가 어느 단계에서 시작되지 못했는지 봅니다.
192 | 
193 | ---
194 | 
195 | # 5. Backend — `online`은 실제 Storage 연결의 중요한 중간 증거다
196 | 
197 | > Trident Controller가 떠 있어도 어떤 NetApp Storage를 사용할지 연결되지 않으면 PVC를 실제 Volume으로 공급할 수 없습니다.
198 | 
199 | Backend는 다음 역할을 한다.
200 | 
201 | ```text
202 | Trident
203 | → Backend
204 | → 승인 SVM·Management/Data LIF·Storage 정책
205 | → 실제 Volume 공급
206 | ```
207 | 
208 | 확인할 질문:
209 | 
210 | ```text
211 | 현재 신규 Member용 Backend인가
212 | Backend state가 online인가
213 | 승인 SVM과 Data LIF를 가리키는가
214 | 승인 Driver·Protocol과 맞는가
215 | Credential이 승인된 관리 경로를 사용하는가
216 | ```
217 | 
218 | 정확한 Backend 생성·Credential 입력은 Storage Runbook을 따른다.
219 | 
220 | ## 5.1 `online`의 증거 범위
221 | 
222 | ```text
223 | Backend online
224 | → Trident와 Backend의 기본 관리 연결이 성립
225 | ```
226 | 
227 | 하지만:
228 | 
229 | ```text
230 | Backend online
231 | ≠ StorageClass 정책 정상
232 | ≠ PVC Provisioning 성공
233 | ≠ Pod Node에서 NFS Mount 가능
234 | ≠ Container Write·Read 가능
235 | ```
236 | 
237 | > `online`을 오후 전체 Storage 성공으로 확대하지 않습니다.
238 | 
239 | ## 5.2 Backend가 offline이면 오후로 넘어가지 않는다
240 | 
241 | 첫 확인 범위:
242 | 
243 | ```text
244 | Backend 대상 SVM·LIF
245 | Network 접근
246 | 승인 Credential 경로
247 | Driver·Protocol
248 | Trident Log·Backend 오류
249 | ```
250 | 
251 | > Pod를 만들어 실패를 더 쌓지 않습니다. 공급 경로가 아직 성립하지 않은 상태입니다.
252 | 
253 | ---
254 | 
255 | # 6. StorageClass — 사용자가 선택할 정책을 실제 Backend와 연결한다
256 | 
257 | > StorageClass는 Storage 자체가 아니라 PVC가 어떤 공급 방식을 사용할지 정하는 Kubernetes 정책 객체입니다.
258 | 
259 | 확인할 핵심값:
260 | 
261 | ```text
262 | 이름
263 | provisioner
264 | Backend·Driver와 연결되는 parameter
265 | reclaimPolicy
266 | volumeBindingMode
267 | allowVolumeExpansion 등 현재 정책
268 | ```
269 | 
270 | 정확한 값은 현재 승인 설계와 Storage Runbook을 따른다.
271 | 
272 | ## 6.1 존재와 정책 정상은 다르다
273 | 
274 | ```text
275 | StorageClass 존재
276 | ≠ 승인 Provisioner
277 | 
278 | 기본 StorageClass 표시
279 | ≠ 이번 Monitoring·Application이 사용해야 할 정책
280 | 
281 | 이름이 기존 Cluster와 같음
282 | ≠ 현재 Backend와 같은 정책
283 | ```
284 | 
285 | > YAML이 문법상 맞다는 것보다 **9월 3일 Monitoring이 실제로 이 StorageClass를 사용해도 되는가**가 중요합니다.
286 | 
287 | ## 6.2 reclaimPolicy는 정리 동작과 연결된다
288 | 
289 | > 오후 Test PVC 삭제 후 PV와 Backend Volume이 어떻게 정리되는지는 StorageClass의 `reclaimPolicy`와 연결됩니다.
290 | 
291 | 따라서 오전에 정책 의미를 알고 오후 Cleanup에서 실제 결과를 확인한다.
292 | 
293 | ```text
294 | reclaimPolicy 값 확인
295 | ≠ 실제 Cleanup 동작 검증 완료
296 | ```
297 | 
298 | ---
299 | 
300 | # 7. 공급 경로를 한 장으로 연결한다
301 | 
302 | 이제 구성요소를 따로 보지 않고 한 경로로 읽는다.
303 | 
304 | ```text
305 | Kubernetes API
306 | → Snapshot 선행 API 준비
307 | → Trident Controller
308 | → Trident Node Plugin
309 | → 승인 Backend online
310 | → 승인 StorageClass
311 | → 오후 PVC 요청을 받을 준비
312 | ```
313 | 
314 | 대조표:
315 | 
316 | ```text
317 | 단계 | 기대 대상 | 실제 상태 | 증거 | 판정
318 | Snapshot CRD | | | |
319 | Snapshot Controller | | | |
320 | Trident Operator | | | |
321 | Trident Controller | | | |
322 | Trident Node Plugin 전체 | | | |
323 | Infra Node Plugin | | | |
324 | Backend | | | |
325 | StorageClass | | | |
326 | ```
327 | 
328 | > 각 행이 초록색처럼 보이는 것이 아니라 **같은 신규 Member와 같은 승인 Storage 설계**를 가리켜야 합니다.
329 | 
330 | ---
331 | 
332 | # 8. 오전에는 PVC를 성공 증거로 미리 만들지 않는다
333 | 
334 | > 오전의 목적은 공급 경로 준비입니다. 실제 PVC·PV·Pod Mount·Write/Read는 오후 대본에서 하나의 통제된 Test Scenario로 수행합니다.
335 | 
336 | 이렇게 분리하는 이유:
337 | 
338 | ```text
339 | 공급 구성 오류
340 | vs
341 | PVC Provisioning 오류
342 | vs
343 | Node Mount 오류
344 | vs
345 | Container 사용 오류
346 | ```
347 | 
348 | 를 섞지 않기 위해서다.
349 | 
350 | > 오전 Component가 불완전한데 Test PVC부터 만들면 Pending과 Event가 추가되어 어디가 원래 첫 실패인지 흐려질 수 있습니다.
351 | 
352 | ---
353 | 
354 | # 9. STORAGE SUPPLY PASS를 판정한다
355 | 
356 | 오전 종료는 두 상태만 사용한다.
357 | 
358 | ## 9.1 STORAGE SUPPLY PASS
359 | 
360 | ```text
361 | KUBERNETES BASE PASS
362 | + 필요한 Snapshot CRD Established
363 | + Snapshot Controller 정상
364 | + Trident Operator·Controller 정상
365 | + Trident Node Plugin이 필요한 전체 Kubernetes Node에서 정상
366 | + 9/3 대상 Infra Node의 Node Plugin 정상
367 | + 승인 Backend online·현재 Member 실제값과 일치
368 | + 승인 StorageClass의 provisioner·정책 일치
369 | + Credential 원문 노출 없음
370 | + Critical Event 없음
371 | ```
372 | 
373 | > 이 판정은 **PVC Test를 시작할 공급 경로가 준비됐다**는 뜻입니다.
374 | 
375 | 아직 증명하지 않은 것:
376 | 
377 | ```text
378 | PVC Bound
379 | PV 생성
380 | Node Mount
381 | NFS 접근
382 | Write·Read
383 | Cleanup
384 | ```
385 | 
386 | ## 9.2 BLOCKED
387 | 
388 | ```text
389 | KUBERNETES BASE가 BLOCKED
390 | Snapshot 필수 CRD·Controller 비정상
391 | Trident Controller 비정상
392 | 필요 Node의 Trident Plugin 누락·비정상
393 | Backend offline 또는 실제 연결 대상 미확정
394 | StorageClass 실제값·정책 미확정
395 | 9/3 Infra Node Storage 경로 선행조건 미확정
396 | Critical Event 원인 미확정
397 | ```
398 | 
399 | > 오후 Test PVC로 확인해 보자는 이유로 BLOCKED를 넘기지 않습니다.
400 | 
401 | ---
402 | 
403 | # 10. 오후 실제 사용 검증으로 넘길 것
404 | 
405 | ```text
406 | Cluster Name·Stage·Context
407 | STORAGE SUPPLY PASS / BLOCKED
408 | Snapshot CRD·Controller 상태
409 | Trident Operator·Controller 상태
410 | Node Plugin 대상·Ready 결과
411 | Backend Name·State·SVM·Data LIF의 비민감 확인 정보
412 | 승인 StorageClass 이름·Provisioner·reclaimPolicy·volumeBindingMode
413 | 9/3 Monitoring 대상 Node Role
414 | Test PVC에 사용할 Namespace·용량 승인 기준
415 | Test Pod 배치 대상·정리 계획
416 | 미해결 항목·담당자
417 | ```
418 | 
419 | > 오후에는 이 공급 경로를 전제로 **PVC → PV → Pod Mount → Write·Read → Cleanup**을 실제로 검증합니다.
420 | 
421 | ---
422 | 
423 | # 11. 마무리 — 오전 Storage를 한 문장으로 다시 말한다
424 | 
425 | > Storage는 StorageClass 하나를 만드는 일이 아닙니다.
426 | >
427 | > Kubernetes의 Storage API가 준비되고, Trident Controller와 Node Plugin이 역할을 수행하며, Trident가 현재 신규 Member의 실제 NetApp Backend에 연결되고, 사용자가 선택할 승인 StorageClass가 그 공급 경로를 표현해야 합니다.
428 | >
429 | > **결국 오전의 성공은 Storage 객체가 많이 보이는 상태가 아니라, 오후 PVC 요청이 실제 승인 Backend로 갈 수 있는 공급 경로가 같은 신규 Member에서 증거로 연결된 상태입니다.**
430 | 
431 | ---
432 | 
433 | # 12. 마지막 Teach-back
434 | 
435 | 1. Snapshotter와 Trident는 왜 같은 Component로 보면 안 되는가?
436 | 2. Trident Controller 정상과 Node Plugin 전체 정상은 무엇이 다른가?
437 | 3. Backend `online`은 무엇을 증명하고 PVC·Mount에 대해서는 무엇을 증명하지 못하는가?
438 | 4. StorageClass 존재와 승인된 Storage 정책은 어떻게 다른가?
439 | 5. `reclaimPolicy`를 오후 Cleanup 결과와 연결해서 봐야 하는 이유는 무엇인가?
440 | 6. Worker 한 대의 Trident Node Plugin 성공을 9월 3일 Infra Node 성공으로 확대하면 안 되는 이유는 무엇인가?
441 | 7. 어떤 상태가 남으면 오후 PVC Test를 시작하면 안 되는가?
442 | 8. `STORAGE SUPPLY PASS`가 증명하는 범위는 어디까지인가?
443 | 
444 | ---
445 | 
446 | # 기준 문서 바로가기
447 | 
448 | - [[출장/30. 구축/2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증|2026-09-02 Member 구축 3일차 기준]]
449 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Kubernetes 스토리지 컴포넌트 구축 및 설치 검증]]
450 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
451 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-02/오후/01. PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본.md

Bytes: 15549
SHA-256: 58fbfe7d83f9337f212b5613cddb0724e8a0dd791b6ea25e7d8728781c5ada65
Lines: 1-551 of 551

```markdown
  1 | ---
  2 | title: "PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-02 Xi'an 신규 Member 구축 3일차 오후 - Storage 실제 사용 검증과 9월 3일 Monitoring 진입 Gate"
  6 | created: "2026-08-28"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 오전의 `STORAGE SUPPLY PASS`를 입력으로 받아 **실제 PVC 요청이 PV로 Provisioning되고, 9월 3일 Monitoring이 배치될 Node에서 Pod가 Volume을 Mount하며, Container가 데이터를 쓰고 다시 읽고, 테스트 삭제 후 정리 동작까지 기대대로 일어나는지 증명하는 법**을 가르친다. 정확한 PVC·Pod Manifest와 Storage 변경 명령은 원본 Storage Runbook을 따른다.
 14 | 
 15 | ## 0. 오전에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage·Context
 19 | STORAGE SUPPLY PASS / BLOCKED
 20 | Snapshotter·Trident 상태
 21 | Node Plugin 대상·Ready
 22 | Backend Name·State·SVM·Data LIF
 23 | StorageClass 이름·Provisioner·reclaimPolicy·volumeBindingMode
 24 | 9/3 Monitoring 대상 Node Role
 25 | Test Namespace·PVC 용량 승인 기준
 26 | 정리 계획
 27 | ```
 28 | 
 29 | > 오전이 `BLOCKED`라면 오후 Test PVC를 만들지 않습니다.
 30 | 
 31 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 32 | 
 33 | > `PVC Bound`를 Storage 완료로 확대하지 않고, **PVC → PV·VolumeHandle → Pod Scheduling Node → Node Mount → Container Filesystem → Write → Read-back → 재읽기 → Cleanup**의 각 성공 단계를 별도 증거로 연결할 수 있어야 한다.
 34 | 
 35 | 오늘의 중심 질문:
 36 | 
 37 | > **실제 Pod가 이 Storage를 Mount하고 데이터를 쓰고 다시 읽으며, 기대한 정리 동작까지 수행할 수 있는가?**
 38 | 
 39 | ---
 40 | 
 41 | # 1. 시작 — `Bound`는 공급 성공이지 사용 성공이 아니다
 42 | 
 43 | 오늘 가장 중요한 구분:
 44 | 
 45 | ```text
 46 | PVC Bound
 47 | → Kubernetes·CSI가 요청을 실제 Volume과 연결하는 단계까지 성공
 48 | 
 49 | Pod Mount 성공
 50 | → 선택된 Node가 실제 Storage 경로를 Container에 붙이는 단계까지 성공
 51 | 
 52 | Write·Read 성공
 53 | → Application이 그 Filesystem을 실제로 사용할 수 있음
 54 | ```
 55 | 
 56 | 따라서:
 57 | 
 58 | ```text
 59 | PVC Bound
 60 | ≠ Pod Mount
 61 | 
 62 | Pod Running
 63 | ≠ 의도한 Volume이 실제 경로에 Mount
 64 | 
 65 | Mount 성공
 66 | ≠ Write 가능
 67 | ```
 68 | 
 69 | > 이 세 경계를 끝까지 분리하는 것이 9월 2일의 핵심입니다.
 70 | 
 71 | ---
 72 | 
 73 | # 2. Test Scenario는 9월 3일 실제 사용 조건과 연결한다
 74 | 
 75 | > 편한 Worker 한 대에서만 성공시키는 Test는 9월 3일 Monitoring Storage의 충분한 선행조건이 아닐 수 있습니다.
 76 | 
 77 | Test 조건을 먼저 고정한다.
 78 | 
 79 | ```text
 80 | Test Namespace: _________________________________________
 81 | StorageClass: ____________________________________________
 82 | PVC 요청 용량: __________________________________________
 83 | AccessMode: ______________________________________________
 84 | Test Pod Image: __________________________________________
 85 | Test Pod 배치 Role: ______________________________________
 86 | 9/3 Monitoring 배치 Role과 관계: _________________________
 87 | Write할 고유 Test File: __________________________________
 88 | Cleanup 시 기대 reclaim 동작: ____________________________
 89 | 승인자·실행자: __________________________________________
 90 | ```
 91 | 
 92 | 원칙:
 93 | 
 94 | ```text
 95 | 9/3 Monitoring이 Infra Node에 배치된다면
 96 | → Infra Storage 경로를 실제로 검증
 97 | ```
 98 | 
 99 | > Role별 NFS Route·Firewall·Export Policy가 다를 수 있으므로 다른 Role의 성공을 자동 확대하지 않습니다.
100 | 
101 | ---
102 | 
103 | # 3. PVC — 요청과 Event를 함께 본다
104 | 
105 | 승인된 Runbook의 Test PVC Manifest를 적용한다.
106 | 
107 | 먼저 확인할 질문:
108 | 
109 | ```text
110 | 의도한 Namespace인가
111 | 의도한 StorageClass인가
112 | 의도한 요청 용량인가
113 | AccessMode가 승인 용도와 맞는가
114 | ```
115 | 
116 | 대표 조회:
117 | 
118 | ```bash
119 | kubectl -n <test-namespace> get pvc -o wide
120 | kubectl -n <test-namespace> describe pvc <test-pvc>
121 | ```
122 | 
123 | ## 3.1 PVC Pending이면 아직 Mount 문제가 아니다
124 | 
125 | ```text
126 | PVC Pending
127 | → Provisioning 경로에서 아직 Volume 할당이 완료되지 않음
128 | ```
129 | 
130 | 첫 확인:
131 | 
132 | ```text
133 | StorageClass 이름·Provisioner
134 | PVC Event
135 | Trident Controller 상태
136 | Backend state
137 | Quota·요청 조건
138 | volumeBindingMode와 Scheduling 선행조건
139 | ```
140 | 
141 | > Pending인데 Worker Route나 NFS Export Policy부터 보지 않습니다. 아직 Node Mount 단계에 도달하지 않았을 수 있습니다.
142 | 
143 | ---
144 | 
145 | # 4. PVC Bound — 대응 PV와 실제 Volume Identity를 연결한다
146 | 
147 | PVC가 Bound되면 다음을 확인한다.
148 | 
149 | ```text
150 | PVC 이름
151 | → 연결된 PV 이름
152 | → StorageClass
153 | → Capacity·AccessMode
154 | → CSI Driver
155 | → VolumeHandle
156 | → 실제 Storage Volume·Export를 식별할 근거
157 | ```
158 | 
159 | 대표 조회:
160 | 
161 | ```bash
162 | kubectl -n <test-namespace> get pvc <test-pvc> -o yaml
163 | kubectl get pv <bound-pv> -o yaml
164 | ```
165 | 
166 | > Secret Data나 Credential은 출력·증적에서 마스킹합니다.
167 | 
168 | ## 4.1 Bound의 증거 범위
169 | 
170 | ```text
171 | PVC Bound
172 | → Provisioning 성공
173 | → PVC와 PV 연결
174 | ```
175 | 
176 | 하지만:
177 | 
178 | ```text
179 | PVC Bound
180 | ≠ 어느 Node에서도 NFS Mount 가능
181 | ```
182 | 
183 | > 이제부터 실패 경계가 공급 경로에서 실제 소비 Node 경로로 이동합니다.
184 | 
185 | ---
186 | 
187 | # 5. Test Pod — 어느 Node에서 Mount를 시도하는지 먼저 고정한다
188 | 
189 | 승인된 Test Pod Manifest는 PVC를 실제 Container 경로에 Mount하고, 9월 3일 사용 조건과 가능한 한 같은 Role에 배치한다.
190 | 
191 | 확인:
192 | 
193 | ```bash
194 | kubectl -n <test-namespace> get pod <test-pod> -o wide
195 | kubectl -n <test-namespace> describe pod <test-pod>
196 | ```
197 | 
198 | 먼저 기록한다.
199 | 
200 | ```text
201 | Pod: _____________________________________________________
202 | Scheduled Node: __________________________________________
203 | Node Role: _______________________________________________
204 | PVC: _____________________________________________________
205 | Container MountPath: _____________________________________
206 | Pod Status: ______________________________________________
207 | Event의 Storage 관련 문장: _______________________________
208 | ```
209 | 
210 | > Mount 실패를 조사할 때 **어느 Node가 Source가 되어 어느 NFS 경로를 붙이려 했는지**가 핵심입니다.
211 | 
212 | ---
213 | 
214 | # 6. `Bound + FailedMount`는 모순이 아니다
215 | 
216 | ```text
217 | PVC Bound
218 | → Volume 준비 성공
219 | 
220 | Pod FailedMount
221 | → 선택된 Node의 실제 Mount 경로 실패
222 | ```
223 | 
224 | 따라서 다음 질문으로 이동한다.
225 | 
226 | ```text
227 | Event가 요청한 Server·Path는 무엇인가
228 | PV·CSI 정의와 같은가
229 | Pod가 어느 Node에 배치됐는가
230 | 그 Node Source IP에서 Data LIF까지 Route가 있는가
231 | TCP 2049 경로가 가능한가
232 | Export Policy가 실제 Source를 허용하는가
233 | ```
234 | 
235 | ## 6.1 Kubernetes·Network·ONTAP 책임 경계를 분리한다
236 | 
237 | | 관찰 | 다음 확인 영역 |
238 | |---|---|
239 | | PVC Pending | Kubernetes·Trident Provisioning |
240 | | Server·Path 정의 불일치 | Kubernetes Object·Trident |
241 | | Route 없음·Timeout | Node Network |
242 | | TCP 2049 불가 | Network·Firewall |
243 | | `access denied by server` | 실제 Source IP·Export Policy |
244 | | Mount option 오류 | PV·StorageClass·Node Mount 조건 |
245 | 
246 | > 원본 6.3 Troubleshooting Guide와 연결하되, 과거 사례의 원인을 현재 장애의 확정 원인으로 복사하지 않습니다.
247 | 
248 | ---
249 | 
250 | # 7. Pod Running 뒤에 실제 Mount를 확인한다
251 | 
252 | > Pod가 Running이면 좋지만 Volume이 의도한 경로에 실제 Mount됐는지 별도 확인합니다.
253 | 
254 | Container 내부에서 현재 Runbook이 승인한 명령으로 확인한다.
255 | 
256 | 예:
257 | 
258 | ```text
259 | Filesystem·MountPath 확인
260 | → 기대 Volume이 해당 경로에 연결됐는가
261 | ```
262 | 
263 | 대표적인 확인 도구는 `df`, `mount`, `findmnt` 등이지만 현재 Image에 존재하는 승인 Tool을 사용한다.
264 | 
265 | 구분:
266 | 
267 | ```text
268 | Pod Running
269 | ≠ MountPath가 기대 Volume
270 | ```
271 | 
272 | > Application이 Volume 없이도 시작될 수 있는 구조라면 특히 이 확인이 중요합니다.
273 | 
274 | ---
275 | 
276 | # 8. Write·Read-back — Application 사용 가능성을 실제로 증명한다
277 | 
278 | > Mount만 됐다고 데이터 사용이 가능한 것은 아닙니다. Filesystem 권한, Export 정책, Mount option 등의 문제로 쓰기가 실패할 수 있습니다.
279 | 
280 | 승인된 고유 Test File 하나만 사용한다.
281 | 
282 | 원칙:
283 | 
284 | ```text
285 | 고유 파일명
286 | 기존 파일 덮어쓰기 금지
287 | 작은 Test Data
288 | 비민감 내용
289 | 정리 계획
290 | ```
291 | 
292 | 검증 흐름:
293 | 
294 | ```text
295 | MountPath에 Test File Write
296 | → 즉시 Read-back
297 | → 내용 일치 확인
298 | ```
299 | 
300 | 증거:
301 | 
302 | ```text
303 | Write 성공
304 | + Read-back 내용 일치
305 | ```
306 | 
307 | 하지만:
308 | 
309 | ```text
310 | 한 번의 Write·Read
311 | ≠ 재시작 뒤에도 같은 Storage 사용을 완전히 증명
312 | ```
313 | 
314 | ---
315 | 
316 | # 9. 가능하면 재읽기로 영속 경계를 확인한다
317 | 
318 | > 테스트 영향과 일정이 허용되면 승인된 방식으로 Pod를 재생성하거나 별도 Reader Pod를 사용해 같은 PVC를 다시 Mount하고 기존 Test File을 읽습니다.
319 | 
320 | 이 단계가 답하는 질문:
321 | 
322 | ```text
323 | Container Process의 로컬 파일이 아니라
324 | 실제 Persistent Volume에 기록됐는가
325 | ```
326 | 
327 | 구분:
328 | 
329 | ```text
330 | 같은 Container에서 즉시 Read 성공
331 | ≠ 새 Pod에서도 데이터 유지
332 | ```
333 | 
334 | > 재생성 방식과 영향은 Runbook을 따른다. 운영 Workload를 임의 재시작하지 않습니다.
335 | 
336 | ---
337 | 
338 | # 10. 한 Node 성공을 전체 Role 성공으로 확대하지 않는다
339 | 
340 | 9월 3일 Monitoring Pod가 특정 Infra Node군에 배치될 수 있다면 필요한 범위를 판단한다.
341 | 
342 | ```text
343 | Worker Test 성공
344 | ≠ Infra Node NFS 경로 성공
345 | ```
346 | 
347 | 가능한 검증 방식:
348 | 
349 | ```text
350 | 9/3 실제 배치 대상 Role의 대표 Node에서 Test
351 | 또는
352 | 모든 잠재 배치 Node의 Route·2049·Trident Node Plugin 조건을 별도 확인
353 | ```
354 | 
355 | > 어떤 범위를 실제 Pod Mount로 검증해야 하는지는 현재 배치 정책과 Replica 수를 기준으로 정합니다.
356 | 
357 | ---
358 | 
359 | # 11. Test PVC 성공과 9월 3일 Monitoring PVC 성공을 구분한다
360 | 
361 | 같은 StorageClass를 써도 다음 조건이 다를 수 있다.
362 | 
363 | ```text
364 | Namespace
365 | PVC 요청 용량
366 | Quota
367 | AccessMode
368 | volumeBindingMode
369 | Pod Node Selector·Taint
370 | 실제 배치 Node
371 | ```
372 | 
373 | 따라서:
374 | 
375 | ```text
376 | Test PVC·Pod 성공
377 | → Storage 기반 기능 증거
378 | ```
379 | 
380 | 하지만:
381 | 
382 | ```text
383 | Test 성공
384 | ≠ 모든 Monitoring PVC 자동 성공
385 | ```
386 | 
387 | 9월 3일용으로 별도 확정할 것:
388 | 
389 | ```text
390 | Monitoring Namespace
391 | Prometheus PVC 용량
392 | Alertmanager PVC 용량
393 | Grafana PVC 필요 여부·용량
394 | 사용 StorageClass
395 | 배치 Node Role
396 | Quota·정책
397 | ```
398 | 
399 | ---
400 | 
401 | # 12. Cleanup — 삭제 요청과 실제 정리를 구분한다
402 | 
403 | > Test 성공 뒤 Resource를 삭제할 때도 Storage 동작을 검증할 기회입니다.
404 | 
405 | 정리 전에 증거를 보존한다.
406 | 
407 | ```text
408 | PVC·PV 이름
409 | VolumeHandle
410 | Pod·Node
411 | NFS source/export path
412 | Write·Read 결과
413 | Test File 이름
414 | ```
415 | 
416 | 그다음 승인된 Runbook으로 Test Pod와 PVC를 삭제한다.
417 | 
418 | 확인:
419 | 
420 | ```text
421 | Pod 제거
422 | PVC 제거
423 | PV 상태 변화
424 | Backend Volume 상태
425 | reclaimPolicy 기대 동작
426 | 잔여 Test Resource 없음
427 | ```
428 | 
429 | ## 12.1 reclaimPolicy와 실제 결과
430 | 
431 | ```text
432 | reclaimPolicy=Delete 등 승인 정책
433 | ≠ Delete 요청 즉시 Backend Volume 정리 완료
434 | ```
435 | 
436 | > 실제 PV·Backend Volume이 기대 상태로 전환됐는지 확인합니다.
437 | 
438 | ## 12.2 정리 위험이 보이면 강제 삭제하지 않는다
439 | 
440 | ```text
441 | 예상과 다른 PV가 연결됨
442 | 기존 데이터 Volume으로 보임
443 | 삭제 대상 식별 불명확
444 | Backend Volume 잔여 원인 미확정
445 | ```
446 | 
447 | 이면 추가 삭제를 멈춘다.
448 | 
449 | ---
450 | 
451 | # 13. STORAGE PASS를 판정한다
452 | 
453 | 9월 2일 종료는 두 상태만 사용한다.
454 | 
455 | ## 13.1 STORAGE PASS
456 | 
457 | ```text
458 | STORAGE SUPPLY PASS
459 | + Test PVC가 승인 StorageClass로 Bound
460 | + 대응 PV·CSI Driver·VolumeHandle 확인
461 | + Test Pod가 9/3 사용 조건과 관련된 Node에 배치
462 | + Pod Event에 미해결 FailedMount 없음
463 | + 실제 Volume Mount 확인
464 | + Container Write 성공
465 | + Read-back 내용 일치
466 | + 승인 범위에서 영속 재읽기 확인
467 | + 필요한 Monitoring 배치 Role의 Storage 경로 확인
468 | + Cleanup·reclaim 동작 기대대로 확인
469 | + 9/3 Monitoring StorageClass·Namespace·용량 확정
470 | + Critical Storage Error 없음
471 | ```
472 | 
473 | > 이 판정은 **9월 3일 Monitoring·KubeSphere가 사용할 Storage 기반을 시작할 수 있음**을 뜻합니다.
474 | 
475 | ## 13.2 BLOCKED
476 | 
477 | ```text
478 | PVC Pending 원인 미해결
479 | PV·VolumeHandle 실제값 불일치
480 | Pod FailedMount 미해결
481 | 9/3 대상 Node에서 NFS 경로 미검증·실패
482 | MountPath 실제 Volume 확인 실패
483 | Write 또는 Read-back 실패
484 | 필요한 영속성 확인 실패
485 | Cleanup·reclaim 동작 위험 미확정
486 | Monitoring StorageClass·Namespace·용량 미확정
487 | Kubernetes·Network·ONTAP 중 담당 경계 미확정으로 핵심 기능 차단
488 | ```
489 | 
490 | > BLOCKED 상태에서 9월 3일 Monitoring Stack을 올려 실패 원인을 더 복잡하게 만들지 않습니다.
491 | 
492 | ---
493 | 
494 | # 14. 9월 3일로 넘길 증거
495 | 
496 | ```text
497 | Cluster Name·Stage·Context
498 | STORAGE PASS / BLOCKED
499 | StorageClass 이름·핵심 정책
500 | Backend Name·online 증거
501 | Trident Node Plugin 범위
502 | Test PVC·PV·VolumeHandle
503 | Test Pod·Scheduled Node·Role
504 | NFS source/export path의 비민감 식별 정보
505 | Mount 확인
506 | Write·Read-back·재읽기 결과
507 | Cleanup·PV·Backend Volume 결과
508 | Monitoring Namespace
509 | Prometheus·Alertmanager·Grafana PVC 용량 기준
510 | Monitoring 배치 Node Role
511 | 미해결 Storage 항목·담당자
512 | ```
513 | 
514 | > 9월 3일 첫 블록은 이 결과를 입력으로 받아 Monitoring Storage를 구성합니다.
515 | 
516 | ---
517 | 
518 | # 15. 마무리 — Storage 완료를 한 문장으로 다시 말한다
519 | 
520 | > StorageClass가 보이고 PVC가 Bound되는 것은 중요한 중간 성공입니다.
521 | >
522 | > 하지만 실제 Application이 Storage를 사용하려면 Pod가 배치된 Node에서 CSI와 NFS 경로가 성립하고, Container의 MountPath에 실제 Filesystem이 붙으며, 데이터를 쓰고 다시 읽을 수 있어야 합니다.
523 | >
524 | > 테스트가 끝난 뒤에는 PVC·PV와 Backend Volume의 정리 동작도 승인 정책과 맞아야 합니다.
525 | >
526 | > **결국 9월 2일 완료는 PVC 상태가 Bound인 화면이 아니라, 9월 3일 실제 플랫폼 Workload와 같은 조건에서 Storage를 Mount·Write·Read하고 안전하게 정리할 수 있음을 증명한 상태입니다.**
527 | 
528 | ---
529 | 
530 | # 16. 마지막 Teach-back
531 | 
532 | 1. PVC `Bound`는 정확히 어디까지의 성공을 뜻하는가?
533 | 2. `Bound + FailedMount`가 동시에 가능한 이유는 무엇인가?
534 | 3. Pod가 어느 Node에 배치됐는지를 Mount 장애에서 먼저 확인해야 하는 이유는 무엇인가?
535 | 4. NFS Mount 실패에서 Route·TCP 2049·Source IP·Export Policy는 어떻게 연결되는가?
536 | 5. Pod Running 뒤에도 실제 MountPath를 확인해야 하는 이유는 무엇인가?
537 | 6. Write와 Read-back을 별도로 확인해야 하는 이유는 무엇인가?
538 | 7. Test PVC 성공을 Monitoring PVC 성공으로 자동 확대하면 안 되는 이유는 무엇인가?
539 | 8. Worker의 성공을 Infra Node 성공으로 확대하면 안 되는 경우는 언제인가?
540 | 9. Cleanup과 reclaim 결과가 Storage 검증의 일부인 이유는 무엇인가?
541 | 10. 어떤 조건이 남으면 9월 3일을 BLOCKED해야 하는가?
542 | 
543 | ---
544 | 
545 | # 기준 문서 바로가기
546 | 
547 | - [[출장/30. 구축/2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증|2026-09-02 Member 구축 3일차 기준]]
548 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Kubernetes 스토리지 컴포넌트 구축 및 설치 검증]]
549 | - [[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|NFS PVC Mount 실패]]
550 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
551 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오전/01. Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본.md

Bytes: 17704
SHA-256: 10d98976fc868804e465384d99a83204ee55f5a2a1a95544df8455fedae794d9
Lines: 1-658 of 658

```markdown
  1 | ---
  2 | title: "Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-03 Xi'an 신규 Member 구축 4일차 오전 - Member Monitoring 구성·기능 검증과 KubeSphere 진입 Gate"
  6 | created: "2026-08-28"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 9월 2일 `STORAGE PASS`를 입력으로 받아 **현재 신규 Member의 Metric이 실제로 수집·저장·조회·표시되고, External ETCD와 Monitoring Ingress까지 기능으로 연결되는지 증명하는 법**을 가르친다. Prometheus Operator CRD, custom Stack Manifest, Secret 생성·적용의 정확한 절차는 Member Monitoring Runbook에서 수행한다. 이 대본은 리소스가 많이 Running인지를 세는 문서가 아니라 **각 Endpoint·Label·Storage·Target이 같은 신규 Member를 가리키는지 판정하는 문서**다.
 14 | 
 15 | ## 0. 9월 2일에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage·Context
 19 | STORAGE PASS / BLOCKED
 20 | StorageClass 이름·정책
 21 | Backend·Trident 정상 증거
 22 | Monitoring Namespace 기준
 23 | Prometheus·Alertmanager·Grafana PVC 용량 기준
 24 | Monitoring 배치 Node Role
 25 | 9/3 대상 Node의 Storage Mount 경로 증거
 26 | Registry·Image 공급 기준
 27 | External ETCD Endpoint 기준
 28 | VIP-B·Domain
 29 | ```
 30 | 
 31 | > `STORAGE PASS`가 아니면 Monitoring Stack을 적용하지 않습니다. Storage 실패를 Monitoring 설치 실패로 보이게 만들지 않습니다.
 32 | 
 33 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 34 | 
 35 | > Prometheus Operator CRD, Monitoring Pod, PVC, Service, External ETCD ServiceMonitor와 Grafana가 **각각 무엇을 증명하고 무엇은 증명하지 못하는지** 구분하고, `Pod Running`이 아니라 **Target UP·Query·현재 Member Label·Ingress 실제 기능**으로 Monitoring 완료를 판정할 수 있어야 한다.
 36 | 
 37 | 오늘의 중심 질문:
 38 | 
 39 | > **현재 신규 Member의 Metric이 실제로 수집·저장·조회·표시되고 있으며, 그 Metric이 다른 Cluster가 아니라 바로 이 Member 것이라는 것을 무엇으로 증명할 것인가?**
 40 | 
 41 | ---
 42 | 
 43 | # 1. 시작 — Monitoring은 Pod를 띄우는 일이 아니라 관측 경로를 만드는 일이다
 44 | 
 45 | 전체 흐름을 먼저 본다.
 46 | 
 47 | ```text
 48 | 현재 Member Kubernetes·Storage
 49 | → monitoring Namespace
 50 | → ETCD 인증정보의 안전한 참조
 51 | → Monitoring PVC
 52 | → Prometheus Operator CRD
 53 | → Prometheus Operator
 54 | → Prometheus·Alertmanager·Grafana 등 Stack
 55 | → Service·Endpoint
 56 | → ServiceMonitor·Target
 57 | → Prometheus Query
 58 | → Grafana Datasource·Dashboard
 59 | → Monitoring Ingress·VIP-B
 60 | ```
 61 | 
 62 | > 여기서 핵심은 한 단계의 존재를 뒤 단계의 성공으로 확대하지 않는 것입니다.
 63 | 
 64 | 반드시 구분한다.
 65 | 
 66 | ```text
 67 | CRD Apply 성공
 68 | ≠ Established
 69 | 
 70 | Prometheus Pod Running
 71 | ≠ Target UP
 72 | 
 73 | PVC Bound
 74 | ≠ Monitoring Pod Mount·데이터 기록
 75 | 
 76 | Grafana UI 열림
 77 | ≠ Datasource·Query 정상
 78 | 
 79 | Ingress 존재
 80 | ≠ VIP-B 사용자 경로 정상
 81 | ```
 82 | 
 83 | ---
 84 | 
 85 | # 2. 현재 Member Identity를 Monitoring 값 전체의 기준으로 고정한다
 86 | 
 87 | 먼저 한 장에 적는다.
 88 | 
 89 | ```text
 90 | current-context: _________________________________________
 91 | Cluster Name: ____________________________________________
 92 | Stage: ___________________________________________________
 93 | Monitoring Namespace: ___________________________________
 94 | StorageClass: ____________________________________________
 95 | Registry·Project·Tag 기준: _______________________________
 96 | External ETCD Endpoint: _________________________________
 97 | External Label cluster: _________________________________
 98 | External Label stage: ___________________________________
 99 | VIP-B·Monitoring FQDN: __________________________________
100 | Infra Node Role·Label: ___________________________________
101 | ```
102 | 
103 | > Secret Data, ETCD Client Key, Password, Token은 기록하지 않습니다.
104 | 
105 | ## 2.1 Monitoring 복붙 오적용을 막는 가장 강한 규율
106 | 
107 | ```text
108 | Manifest가 Apply 됨
109 | ≠ 현재 Member 값으로 Apply 됨
110 | ```
111 | 
112 | 반드시 현재 Member와 대조할 값:
113 | 
114 | ```text
115 | externalLabels.cluster
116 | externalLabels.stage
117 | ETCD Endpoints
118 | StorageClass
119 | Ingress Host
120 | Grafana Datasource
121 | Registry·Image Tag
122 | Node Selector·Toleration
123 | KubeSphere가 나중에 참조할 Prometheus Endpoint
124 | ```
125 | 
126 | > 과거 Host·PRD·DEV Member의 값이 하나라도 실행값으로 남아 있다면 적용 전에 멈춥니다.
127 | 
128 | ---
129 | 
130 | # 3. Preliminary — Namespace·Secret·PVC는 Stack보다 먼저 닫는다
131 | 
132 | ## 3.1 monitoring Namespace
133 | 
134 | ```text
135 | Namespace Active
136 | ≠ 이후 Resource가 모두 올바른 Namespace에 있음
137 | ```
138 | 
139 | > 이후 Secret, PVC, ServiceMonitor, Grafana 설정이 현재 `monitoring` Namespace를 사용해야 합니다.
140 | 
141 | ## 3.2 ETCD Certificate Secret
142 | 
143 | > External ETCD Metric을 HTTPS로 Scrape하려면 Prometheus가 승인된 인증 재료를 참조할 수 있어야 합니다.
144 | 
145 | 확인할 것은 내용이 아니라 구조다.
146 | 
147 | ```text
148 | Secret 존재
149 | Namespace = monitoring
150 | Type 확인
151 | 필요 Key 이름 존재
152 | 현재 Member ETCD Certificate와 대응하는 승인 근거
153 | Pod가 참조할 수 있는 경로
154 | ```
155 | 
156 | 반드시 구분한다.
157 | 
158 | ```text
159 | Secret 이름 동일
160 | ≠ 현재 Member Certificate
161 | ```
162 | 
163 | > Secret Data를 Base64 Decode해 교육 화면에 출력하지 않습니다.
164 | 
165 | ## 3.3 Monitoring PVC 선행조건
166 | 
167 | Prometheus·Alertmanager·Grafana가 사용하는 PVC는 9월 2일 Storage 결과를 이어받는다.
168 | 
169 | 확인:
170 | 
171 | ```text
172 | StorageClass
173 | 요청 용량
174 | Namespace Quota
175 | AccessMode
176 | 실제 PVC Bound
177 | Pod가 배치될 Infra Node의 Mount 경로
178 | ```
179 | 
180 | 구분:
181 | 
182 | ```text
183 | Grafana PVC 성공
184 | ≠ Prometheus·Alertmanager PVC 자동 성공
185 | ```
186 | 
187 | > 각각의 요청 용량·Pod 배치·Mount 결과를 확인합니다.
188 | 
189 | ---
190 | 
191 | # 4. Prometheus Operator CRD — Apply보다 Established가 중요하다
192 | 
193 | > Prometheus, ServiceMonitor, PrometheusRule 같은 객체는 Kubernetes 기본 Kind가 아닙니다. 먼저 API가 그 종류를 이해해야 합니다.
194 | 
195 | 흐름:
196 | 
197 | ```text
198 | CRD Apply
199 | → Names Accepted
200 | → Established=True
201 | → API Discovery 가능
202 | → Custom Resource 적용 가능
203 | ```
204 | 
205 | 확인할 질문:
206 | 
207 | ```text
208 | 현재 Bundle이 요구하는 CRD인가
209 | Established=True인가
210 | Served·Storage Version이 현재 Manifest와 맞는가
211 | 과거 Version 충돌이 없는가
212 | ```
213 | 
214 | 반드시 구분한다.
215 | 
216 | ```text
217 | kubectl apply 성공
218 | ≠ CRD Established
219 | ```
220 | 
221 | > CRD가 불완전한데 Operator·Stack을 먼저 올려 반복 오류를 쌓지 않습니다.
222 | 
223 | ---
224 | 
225 | # 5. Monitoring Stack — Running 개수가 아니라 실제 기능 경로를 본다
226 | 
227 | 현재 Bundle의 정확한 Component 목록은 Runbook을 따른다.
228 | 
229 | 대표 역할:
230 | 
231 | ```text
232 | Prometheus Operator
233 | → Prometheus 계열 Custom Resource를 실제 Workload로 조정
234 | 
235 | Prometheus
236 | → Metric Scrape·저장·Query
237 | 
238 | Alertmanager
239 | → Alert 수신·Grouping·Routing
240 | 
241 | Grafana
242 | → Prometheus 등을 Datasource로 Query해 Dashboard 표시
243 | 
244 | kube-state-metrics·Node Exporter 등
245 | → Kubernetes·Node Metric 제공
246 | ```
247 | 
248 | ## 5.1 Cluster Identity Label
249 | 
250 | Monitoring의 가장 중요한 실제값 중 하나:
251 | 
252 | ```text
253 | externalLabels.cluster = 현재 Member Cluster
254 | externalLabels.stage = 현재 Stage
255 | ```
256 | 
257 | 구분:
258 | 
259 | ```text
260 | Prometheus 정상 실행
261 | ≠ Metric Label이 현재 Member
262 | ```
263 | 
264 | > 다른 Cluster Label을 복사하면 Pod는 정상이어도 Multi-Cluster Query와 Dashboard가 잘못된 Cluster로 보입니다.
265 | 
266 | ---
267 | 
268 | # 6. Storage와 Node 배치는 실제 Pod에서 확인한다
269 | 
270 | ## 6.1 PVC Bound 뒤 실제 Mount
271 | 
272 | ```text
273 | Monitoring PVC Bound
274 | ≠ Prometheus·Grafana가 실제 Volume 사용
275 | ```
276 | 
277 | 확인:
278 | 
279 | ```text
280 | Pod가 실제 어느 Infra Node에 배치됐는가
281 | PVC와 PV는 무엇인가
282 | Event에 FailedMount가 없는가
283 | Container의 Storage 경로가 실제 Volume인가
284 | Restart 후에도 Storage 관련 오류가 없는가
285 | ```
286 | 
287 | > 9월 2일 Test 성공을 Monitoring PVC 자동 성공으로 확대하지 않습니다.
288 | 
289 | ## 6.2 Node Selector·Taint·Toleration
290 | 
291 | ```text
292 | Manifest에 nodeSelector 존재
293 | ≠ 실제 Pod가 Infra Node 배치
294 | ```
295 | 
296 | 실제 Pod의 `NODE`를 확인하고, Taint·Toleration과 Replica 배치가 승인 정책에 맞는지 본다.
297 | 
298 | > Platform Workload가 Worker로 잘못 배치돼도 Running일 수 있습니다. 배치 정책은 별도 증거입니다.
299 | 
300 | ---
301 | 
302 | # 7. Registry와 Image — Pull 실패를 Monitoring 설정 문제로 만들지 않는다
303 | 
304 | 확인 경로:
305 | 
306 | ```text
307 | Manifest Image 주소
308 | → Registry FQDN·Project·Repository·Tag
309 | → Node CA Trust·Network
310 | → 필요한 Secret
311 | → Pod Event의 실제 Pull 결과
312 | ```
313 | 
314 | 구분:
315 | 
316 | ```text
317 | ImagePullBackOff
318 | ≠ Monitoring Logic 실패
319 | ```
320 | 
321 | > Image Pull 단계에서 실패하면 Prometheus Rule이나 Datasource부터 바꾸지 않습니다.
322 | 
323 | ---
324 | 
325 | # 8. Service·Endpoint — Pod Running 뒤 실제 연결점을 만든다
326 | 
327 | 각 주요 Component에서 최소 다음을 확인한다.
328 | 
329 | ```text
330 | Service 존재
331 | Port·Selector
332 | Endpoint 또는 EndpointSlice
333 | Ready Pod IP와 일치
334 | ```
335 | 
336 | 구분:
337 | 
338 | ```text
339 | Service 존재
340 | ≠ Endpoint 존재
341 | 
342 | Endpoint 존재
343 | ≠ Prometheus Scrape·Grafana Query 정상
344 | ```
345 | 
346 | > 뒤의 ServiceMonitor와 Datasource는 이 Service·Endpoint 위에 올라갑니다.
347 | 
348 | ---
349 | 
350 | # 9. External ETCD Monitoring — 최종 증거는 Target UP이다
351 | 
352 | External ETCD는 Kubernetes Pod Selector로 자동 발견되지 않을 수 있다.
353 | 
354 | 정상 경로:
355 | 
356 | ```text
357 | 현재 Member ETCD IP:Port
358 | → Kubernetes Endpoint 표현
359 | → Service
360 | → ServiceMonitor
361 | → Prometheus
362 | → HTTPS /metrics
363 | → Target UP
364 | ```
365 | 
366 | 각 단계에서 볼 것:
367 | 
368 | ### Endpoint
369 | 
370 | ```text
371 | 현재 Member ETCD IP인가
372 | 승인 Port인가
373 | 다른 Cluster IP 혼입 없음
374 | ```
375 | 
376 | ### Service
377 | 
378 | ```text
379 | Endpoint와 연결되는가
380 | Port Name이 ServiceMonitor와 일치하는가
381 | Namespace가 맞는가
382 | ```
383 | 
384 | ### ServiceMonitor
385 | 
386 | ```text
387 | Selector가 정확한 Service를 선택하는가
388 | Port Name·Scheme·Path가 실제 ETCD와 맞는가
389 | TLS Config가 현재 Secret을 참조하는가
390 | ```
391 | 
392 | ### Target
393 | 
394 | 최종적으로:
395 | 
396 | ```text
397 | Health = UP
398 | Last Scrape 정상
399 | Error 없음
400 | 현재 Member Endpoint
401 | 실제 Metric Query 가능
402 | ```
403 | 
404 | ## 9.1 존재와 기능의 차이
405 | 
406 | ```text
407 | Service·Endpoint 존재
408 | ≠ Target UP
409 | 
410 | Target UP
411 | ≠ 다른 Cluster ETCD가 아닌 현재 Member라는 뜻까지 자동 증명
412 | ```
413 | 
414 | > Endpoint IP와 Cluster Label을 같이 대조합니다.
415 | 
416 | ## 9.2 Target Down 첫 분기
417 | 
418 | | 증상 | 첫 확인 |
419 | |---|---|
420 | | No Endpoint | Endpoint·Service Selector |
421 | | Connection refused | ETCD Metric Listen·Port |
422 | | Timeout | Network·Route·Firewall |
423 | | x509 | CA·Client Certificate·Server Name |
424 | | 401/403 | ETCD Auth·Certificate |
425 | | Metric은 오지만 다른 Cluster | Endpoint IP·External Label |
426 | 
427 | > Target Down인데 Prometheus 전체를 재설치하지 않습니다.
428 | 
429 | ---
430 | 
431 | # 10. Prometheus 자체 기능 — Pod Running 뒤 Query까지 본다
432 | 
433 | 확인 범위:
434 | 
435 | ```text
436 | Prometheus Pod Ready
437 | → Service·Endpoint
438 | → Prometheus Web/API
439 | → Target 목록
440 | → Rule Load
441 | → 간단 Query 결과
442 | ```
443 | 
444 | 구분:
445 | 
446 | ```text
447 | Prometheus Pod Running
448 | ≠ Target UP
449 | 
450 | Rule Object 존재
451 | ≠ Prometheus가 Rule Load
452 | ```
453 | 
454 | 간단 Query는 현재 Member에서 실제로 존재하는 Metric을 사용한다. 결과에 현재 Cluster Label이 있는지 함께 본다.
455 | 
456 | > 복잡한 Dashboard보다 낮은 단계의 Prometheus Query가 먼저입니다.
457 | 
458 | ---
459 | 
460 | # 11. Grafana — UI 접속보다 Datasource·Query가 중요하다
461 | 
462 | Grafana 흐름:
463 | 
464 | ```text
465 | Grafana Pod
466 | → Service
467 | → Datasource
468 | → Prometheus Endpoint
469 | → Query
470 | → Dashboard Panel
471 | ```
472 | 
473 | 반드시 구분한다.
474 | 
475 | ```text
476 | Grafana UI 열림
477 | ≠ Datasource 정상
478 | 
479 | Datasource Save & Test 성공
480 | ≠ 모든 Dashboard Variable·Panel 정상
481 | 
482 | Panel에 숫자 있음
483 | ≠ 현재 Member Metric
484 | ```
485 | 
486 | 확인할 것:
487 | 
488 | ```text
489 | Datasource URL이 현재 Monitoring Service인가
490 | Save & Test 성공
491 | 간단 Query 성공
492 | Cluster Label이 현재 Member
493 | Dashboard 최근 데이터 존재
494 | Panel Error 없음
495 | 다른 Cluster Metric 혼입 없음
496 | ```
497 | 
498 | > Grafana Datasource와 이후 KubeSphere external Monitoring Endpoint는 목적이 다를 수 있으므로 이름이 비슷하다고 같은 Endpoint로 추측하지 않습니다.
499 | 
500 | ---
501 | 
502 | # 12. Monitoring Ingress — UI가 실제 VIP-B 경로에서 열리는가
503 | 
504 | 전체 경로:
505 | 
506 | ```text
507 | 운영자
508 | → Monitoring FQDN
509 | → DNS
510 | → Member VIP-B
511 | → Router Ingress Controller
512 | → Monitoring Ingress
513 | → Service
514 | → Endpoint
515 | → Prometheus·Grafana·Alertmanager
516 | ```
517 | 
518 | 확인:
519 | 
520 | ```text
521 | FQDN이 현재 Member Domain인가
522 | DNS가 현재 VIP-B를 반환하는가
523 | Ingress Host·Path·Class가 맞는가
524 | Service·Port가 실제 Component와 맞는가
525 | Backend Endpoint가 존재하는가
526 | 실제 HTTP·HTTPS 응답이 기대 상태인가
527 | ```
528 | 
529 | 구분:
530 | 
531 | ```text
532 | Ingress 객체 존재
533 | ≠ 외부 기능 정상
534 | ```
535 | 
536 | > 다른 Member Domain이나 VIP-B가 들어간 Manifest는 Apply 성공해도 현재 Member 성공이 아닙니다.
537 | 
538 | ---
539 | 
540 | # 13. Monitoring 전체에서 첫 단절을 찾는다
541 | 
542 | | 증상 | 먼저 볼 경계 |
543 | |---|---|
544 | | CRD 관련 오류 | CRD 존재·Established·Version |
545 | | Pod Pending | PVC·Node Selector·Taint·Resource |
546 | | ImagePullBackOff | Registry·Tag·CA·Secret |
547 | | PVC Bound + Pod FailedMount | 9/2 Storage 경로·실제 Node |
548 | | Prometheus Running + Target Down | ServiceMonitor·Service·Endpoint·TLS·Network |
549 | | Grafana UI + Query 실패 | Datasource·Prometheus Service·Query |
550 | | Ingress 존재 + UI 실패 | DNS·VIP-B·Ingress·Service·Endpoint |
551 | | Metric은 보이지만 Cluster가 틀림 | External Label·Endpoint·Datasource |
552 | 
553 | > 리소스 수를 세지 않고 마지막 성공과 첫 실패 사이를 봅니다.
554 | 
555 | ---
556 | 
557 | # 14. MONITORING PASS를 판정한다
558 | 
559 | ## 14.1 MONITORING PASS
560 | 
561 | ```text
562 | STORAGE PASS
563 | + 현재 Member Identity 값 검토 완료
564 | + monitoring Namespace 정상
565 | + ETCD Secret 구조·참조 정상, 원문 미노출
566 | + Monitoring PVC 실제 Mount·사용 정상
567 | + 필요한 Prometheus Operator CRD Established
568 | + Operator·Prometheus·Alertmanager·Grafana 등 핵심 Component 정상
569 | + 실제 Infra 배치 정책 정상
570 | + Service·Endpoint 정상
571 | + 주요 Kubernetes·Node Target 정상
572 | + External ETCD Target UP·현재 Member 확인
573 | + Rule Load 정상
574 | + Prometheus 간단 Query 정상
575 | + Grafana Datasource·Query·현재 Member Dashboard 정상
576 | + Monitoring Ingress·VIP-B 실제 기능 정상
577 | + Cluster·Stage Label 정확
578 | + Critical Event·반복 Restart 없음
579 | ```
580 | 
581 | > 이 상태가 돼야 Member KubeSphere 설치로 넘어갑니다.
582 | 
583 | ## 14.2 BLOCKED
584 | 
585 | ```text
586 | STORAGE가 BLOCKED
587 | Monitoring PVC Mount 실패
588 | CRD Established 실패·Version 충돌
589 | 핵심 Monitoring Pod 반복 실패
590 | External ETCD Target Down 원인 미확정
591 | Grafana가 다른 Cluster Prometheus 참조
592 | External Label 잘못 적용
593 | Registry Image Pull 실패
594 | Ingress가 다른 Domain·VIP 사용
595 | 현재 Member Metric임을 증명할 수 없음
596 | ```
597 | 
598 | > KubeSphere를 먼저 올려 문제를 덮지 않습니다.
599 | 
600 | ---
601 | 
602 | # 15. Member KubeSphere 블록으로 넘길 증거
603 | 
604 | ```text
605 | Cluster Name·Stage·Context
606 | MONITORING PASS / BLOCKED
607 | Monitoring Namespace
608 | StorageClass·실제 PVC Mount 결과
609 | Prometheus Operator CRD 상태
610 | Prometheus·Alertmanager·Grafana 상태
611 | 현재 Member externalLabels
612 | External ETCD Target UP 증거
613 | Prometheus Service·Endpoint
614 | Grafana Datasource·Query 결과
615 | KubeSphere가 사용할 External Monitoring Endpoint 후보·근거
616 | Monitoring Ingress·VIP-B 결과
617 | Infra Node 배치 결과
618 | Registry·Image 기준
619 | 미해결 Monitoring 항목
620 | ```
621 | 
622 | > 다음 블록에서는 이 Monitoring을 KubeSphere가 실제 external Monitoring으로 사용할 수 있는지 확인합니다.
623 | 
624 | ---
625 | 
626 | # 16. 마무리 — Monitoring 완료를 한 문장으로 다시 말한다
627 | 
628 | > Monitoring은 Prometheus와 Grafana Pod를 띄우는 작업이 아닙니다.
629 | >
630 | > 현재 Member의 Storage와 배치 조건 위에서 Prometheus가 실제 Target을 Scrape하고, External ETCD를 현재 Member Endpoint로 관측하며, Query 결과에 올바른 Cluster Identity가 붙고, Grafana가 그 Datasource를 실제로 조회하며, 외부 운영자가 현재 Member VIP-B를 통해 접근할 수 있어야 합니다.
631 | >
632 | > **결국 Monitoring 완료는 Running Pod 개수가 아니라, 현재 신규 Member의 Metric이 끝까지 올바른 Identity로 수집·저장·조회·표시되는 것을 증명한 상태입니다.**
633 | 
634 | ---
635 | 
636 | # 17. 마지막 Teach-back
637 | 
638 | 1. CRD Apply 성공과 `Established=True`는 무엇이 다른가?
639 | 2. Monitoring PVC Bound와 Prometheus 실제 Storage 사용은 왜 다른 증거인가?
640 | 3. Manifest에 Infra nodeSelector가 있다는 것과 실제 Infra 배치는 무엇이 다른가?
641 | 4. Prometheus Pod Running 뒤에도 Target UP과 Query를 확인해야 하는 이유는 무엇인가?
642 | 5. External ETCD Service·Endpoint 존재와 Target UP은 무엇이 다른가?
643 | 6. Target UP이더라도 현재 Member ETCD인지 별도로 확인해야 하는 이유는 무엇인가?
644 | 7. Grafana UI 접속과 Datasource·Query 성공은 어떻게 다른가?
645 | 8. External Label이 잘못돼도 Monitoring Pod가 정상일 수 있는 이유는 무엇인가?
646 | 9. Ingress 존재와 Monitoring 외부 접근 정상은 무엇이 다른가?
647 | 10. 어떤 상태가 남으면 Member KubeSphere 설치를 BLOCKED해야 하는가?
648 | 
649 | ---
650 | 
651 | # 기준 문서 바로가기
652 | 
653 | - [[출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수|2026-09-03 Member 구축 4일차 기준]]
654 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
655 | - [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
656 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
657 | - [[60. 이슈 및 결정/장애/dev-apps-pa01-xas Monitoring 복붙 오적용|Monitoring 복붙 오적용 사례]]
658 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오전/02. Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본.md

Bytes: 14089
SHA-256: ac887b60646514ee9f3cca827aabac853d2a2ca494223256f6fa16c5325929e3
Lines: 1-560 of 560

```markdown
  1 | ---
  2 | title: "Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-03 Xi'an 신규 Member 구축 4일차 오전 - Member KubeSphere 설치·기능 검증과 Host Join 선행 Gate"
  6 | created: "2026-08-28"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 `MONITORING PASS`를 입력으로 받아 **검증된 Storage와 Monitoring을 실제 Member KubeSphere가 사용하고, `clusterRole=member`와 Platform Workload 배치·Console·API가 의도대로 성립했는지 판정하는 법**을 가르친다. `kubesphere-installer.yaml`, ClusterConfiguration과 세부 Module의 정확한 적용 절차는 Member KubeSphere Runbook에서 수행한다.
 14 | 
 15 | ## 0. Monitoring 블록에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage·Context
 19 | MONITORING PASS / BLOCKED
 20 | StorageClass·Monitoring PVC 실제 사용 증거
 21 | Prometheus Service·Endpoint
 22 | External ETCD Target UP
 23 | Grafana Datasource·Query 결과
 24 | Monitoring Ingress·VIP-B
 25 | Infra Node 배치 기준
 26 | Registry·Image 기준
 27 | KubeSphere external Monitoring Endpoint 후보·근거
 28 | ```
 29 | 
 30 | > Monitoring이 BLOCKED라면 KubeSphere 설치로 넘어가지 않습니다. Installer 내부 Monitoring Task에서 같은 실패를 다시 만들지 않습니다.
 31 | 
 32 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 33 | 
 34 | > `ks-installer` Pod Running을 설치 완료로 보지 않고, **Installer 실행기 → ClusterConfiguration 실제값 → 내부 Task → Platform Workload → Storage·Monitoring 연동 → Console·API → member Role**을 독립 증거로 확인해 Host Join 전 Member 자체 정상 여부를 판정할 수 있어야 한다.
 35 | 
 36 | 오늘의 중심 질문:
 37 | 
 38 | > **KubeSphere Installer가 실행된 것이 아니라, 검증된 Storage와 Monitoring을 사용하는 실제 Member Platform이 준비됐는가?**
 39 | 
 40 | ---
 41 | 
 42 | # 1. 시작 — installer와 ClusterConfiguration은 역할이 다르다
 43 | 
 44 | ```text
 45 | kubesphere-installer.yaml
 46 | → KubeSphere 설치를 수행할 실행기·CRD·RBAC·Deployment 준비
 47 | 
 48 | ClusterConfiguration
 49 | → 이 Member에 어떤 기능·Role·Storage·Monitoring·Registry를 구성할지 정의
 50 | ```
 51 | 
 52 | 따라서:
 53 | 
 54 | ```text
 55 | Installer Pod Running
 56 | ≠ ClusterConfiguration의 모든 Task 성공
 57 | ```
 58 | 
 59 | > Host용 Manifest를 복사해 `clusterRole`만 member로 바꾸는 방식은 금지합니다. StorageClass, Monitoring Endpoint, ETCD, Registry, Node 배치와 Domain이 모두 Cluster별 실제값입니다.
 60 | 
 61 | ---
 62 | 
 63 | # 2. 적용 전 Member 핵심값을 한 장에 고정한다
 64 | 
 65 | ```text
 66 | current-context: _________________________________________
 67 | Cluster Name·Stage: _____________________________________
 68 | clusterRole 기대값: member
 69 | StorageClass: ____________________________________________
 70 | Registry·Project·Tag: ____________________________________
 71 | External ETCD: ___________________________________________
 72 | Monitoring Type: _________________________________________
 73 | External Prometheus Endpoint: _____________________________
 74 | Console·Ingress Domain: __________________________________
 75 | Infra Node Selector·Toleration: ___________________________
 76 | Module Enable·Disable 기준: ______________________________
 77 | ```
 78 | 
 79 | 보호된 값은 구조만 확인한다.
 80 | 
 81 | ```text
 82 | Join 관련 Secret·JWT·kubeconfig
 83 | ETCD Certificate Secret
 84 | Registry Credential
 85 | Private Key·Password
 86 | ```
 87 | 
 88 | > 원문은 문서·로그·화면에 남기지 않습니다.
 89 | 
 90 | ## 2.1 현재 Member 값 대조가 Apply보다 먼저다
 91 | 
 92 | ```text
 93 | Manifest 문법 정상
 94 | ≠ 현재 Member 설정 정상
 95 | 
 96 | 과거 Host에서 성공한 ClusterConfiguration
 97 | ≠ 신규 Member에서 사용 가능
 98 | ```
 99 | 
100 | ---
101 | 
102 | # 3. Installer Pod 자체와 내부 Task를 분리한다
103 | 
104 | 먼저 두 실패를 구분한다.
105 | 
106 | ```text
107 | Installer Pod 자체가 Pending·ImagePullBackOff·Crash
108 | vs
109 | Installer는 Running이지만 내부 Task 실패
110 | ```
111 | 
112 | ## 3.1 Installer Pod 자체가 시작되지 않는 경우
113 | 
114 | 첫 확인:
115 | 
116 | | 증상 | 먼저 볼 것 |
117 | |---|---|
118 | | Pending | Node Selector·Taint·PVC·Resource |
119 | | ImagePullBackOff | Registry·Tag·CA·Secret |
120 | | CrashLoopBackOff | Pod Log·Config·권한 |
121 | 
122 | > 내부 Monitoring·Multicluster Task를 보기 전에 실행기 자체가 정상적으로 동작해야 합니다.
123 | 
124 | ## 3.2 Installer Running은 시작점이다
125 | 
126 | ```text
127 | ks-installer Running
128 | → 설치 Task를 수행할 실행기가 준비됨
129 | ```
130 | 
131 | 하지만:
132 | 
133 | ```text
134 | ks-installer Running
135 | ≠ KubeSphere 설치 완료
136 | ```
137 | 
138 | 정확한 완료는 Installer Log와 생성된 Workload·기능으로 확인한다.
139 | 
140 | ---
141 | 
142 | # 4. Installer 로그 — 실패 Task 범위를 먼저 고정한다
143 | 
144 | Installer Log에서 먼저 확인할 것:
145 | 
146 | ```text
147 | 어느 Task 범주인가
148 | 최초 실패는 무엇인가
149 | Monitoring·Multicluster·Network·Common 중 어디인가
150 | 오류 원문은 무엇인가
151 | 앞에서 이미 PASS한 기능과 충돌하는가
152 | ```
153 | 
154 | 대표 Task 범주:
155 | 
156 | ```text
157 | common
158 | monitoring
159 | multicluster
160 | network
161 | logging·events·alerting 등 현재 Bundle Module
162 | ```
163 | 
164 | > 정확한 Task 이름은 현재 로그를 기준으로 합니다.
165 | 
166 | ## 4.1 Monitoring Task 실패
167 | 
168 | 먼저 9월 3일 첫 블록 증거와 연결한다.
169 | 
170 | ```text
171 | External Prometheus Endpoint
172 | Prometheus Service·Endpoint
173 | Monitoring PVC
174 | CRD
175 | 현재 Member Label
176 | ```
177 | 
178 | > Monitoring PASS가 있는데 Installer가 다른 Endpoint를 참조하면 KubeSphere 설정 문제입니다. Storage·Monitoring을 재설치하지 않습니다.
179 | 
180 | ## 4.2 CRD not found
181 | 
182 | ```text
183 | CRD 실제 존재·Established
184 | → Installer가 기대하는 Version·Kind
185 | ```
186 | 
187 | 을 비교한다.
188 | 
189 | ## 4.3 Multicluster Task 실패
190 | 
191 | ```text
192 | clusterRole=member
193 | Join 관련 설정 구조
194 | Host 연결 전제
195 | 보호된 값의 현재 Member 대응 여부
196 | ```
197 | 
198 | 를 먼저 확인한다.
199 | 
200 | ---
201 | 
202 | # 5. ClusterConfiguration의 핵심은 Member 역할과 외부 의존성이다
203 | 
204 | KubeSphere에서 반드시 대조할 연결:
205 | 
206 | ```text
207 | Storage
208 | → 9/2 검증 StorageClass
209 | 
210 | Monitoring
211 | → 오늘 MONITORING PASS한 Prometheus Endpoint
212 | 
213 | Registry
214 | → 현재 Member 승인 Registry·Image
215 | 
216 | External ETCD
217 | → 현재 Member Endpoint·Secret 참조
218 | 
219 | Multi-Cluster Role
220 | → member
221 | 
222 | Platform 배치
223 | → 승인 Infra Node 정책
224 | ```
225 | 
226 | ## 5.1 `clusterRole=member`의 의미
227 | 
228 | ```text
229 | member
230 | → 중앙 Host가 아닌 관리 대상 Member Cluster 역할
231 | ```
232 | 
233 | 구분:
234 | 
235 | ```text
236 | YAML에 member 문자열 존재
237 | ≠ 실제 Member Platform 전체 정상
238 | ```
239 | 
240 | > Role은 Join 전제 중 하나일 뿐입니다.
241 | 
242 | ---
243 | 
244 | # 6. Platform Workload — Manifest 배치 조건과 실제 Pod 배치를 분리한다
245 | 
246 | 확인할 것:
247 | 
248 | ```text
249 | Node Label
250 | Node Taint
251 | Workload nodeSelector
252 | Toleration
253 | Replica 수
254 | 실제 Pod NODE
255 | ```
256 | 
257 | 증거:
258 | 
259 | ```text
260 | Manifest에 Infra Selector 있음
261 | + 실제 Pod가 승인 Infra Node에 배치
262 | + 필요한 Replica 분산
263 | = 배치 정책 반영
264 | ```
265 | 
266 | 하지만:
267 | 
268 | ```text
269 | Pod Running
270 | ≠ 올바른 Node 배치
271 | ```
272 | 
273 | ## 6.1 Pending이면 KubeSphere 자체 오류로 단정하지 않는다
274 | 
275 | ```text
276 | nodeSelector와 실제 Label
277 | Taint·Toleration
278 | PVC Binding
279 | Resource Request
280 | Scheduler Event
281 | ```
282 | 
283 | 순으로 본다.
284 | 
285 | ---
286 | 
287 | # 7. KubeSphere가 실제 Storage를 사용하는가
288 | 
289 | > 9월 2일 Storage PASS와 Monitoring PVC 성공 뒤에도 KubeSphere 자체 PVC는 별도 요청일 수 있습니다.
290 | 
291 | 확인:
292 | 
293 | ```text
294 | KubeSphere 관련 PVC가 승인 StorageClass 사용
295 | Bound
296 | 실제 Pod Mount
297 | FailedMount 없음
298 | 필요한 데이터 경로 사용
299 | ```
300 | 
301 | 구분:
302 | 
303 | ```text
304 | 9/2 Test PVC 성공
305 | ≠ KubeSphere PVC 자동 성공
306 | 
307 | Monitoring PVC 성공
308 | ≠ KubeSphere PVC 자동 성공
309 | ```
310 | 
311 | > Namespace·용량·배치 Node가 다를 수 있습니다.
312 | 
313 | ---
314 | 
315 | # 8. External Monitoring — Endpoint 기재와 실제 사용을 구분한다
316 | 
317 | KubeSphere는 외부 Monitoring을 사용하도록 설정될 수 있다.
318 | 
319 | 정상 경로:
320 | 
321 | ```text
322 | KubeSphere
323 | → External Monitoring Endpoint
324 | → 오늘 검증한 Prometheus Service
325 | → 실제 Query
326 | → 현재 Member Metric 표시
327 | ```
328 | 
329 | 확인:
330 | 
331 | ```text
332 | Endpoint가 현재 Monitoring Service인가
333 | Port·Scheme이 실제 서비스와 맞는가
334 | KubeSphere UI/API에서 Monitoring 데이터가 보이는가
335 | Cluster Identity가 현재 Member인가
336 | ```
337 | 
338 | 구분:
339 | 
340 | ```text
341 | Endpoint 문자열 존재
342 | ≠ KubeSphere Monitoring 기능 정상
343 | ```
344 | 
345 | ---
346 | 
347 | # 9. Console·API — 화면이 열리는 것과 Platform 정상은 다르다
348 | 
349 | 확인 경로:
350 | 
351 | ```text
352 | DNS·VIP-B·Ingress
353 | → KubeSphere Console Service
354 | → Console 응답
355 | → API
356 | → Platform 기능
357 | ```
358 | 
359 | 반드시 구분한다.
360 | 
361 | ```text
362 | Console 열림
363 | ≠ API 정상
364 | 
365 | Console·API 정상
366 | ≠ Storage·Monitoring·Role·Workload 배치 정상
367 | ```
368 | 
369 | > 화면 하나를 최종 증거로 사용하지 않습니다.
370 | 
371 | ---
372 | 
373 | # 10. 주요 Workload는 개수가 아니라 역할과 기능으로 본다
374 | 
375 | 현재 Bundle의 핵심 Platform Workload를 확인한다.
376 | 
377 | 최소 질문:
378 | 
379 | ```text
380 | 필수 Deployment·StatefulSet이 Ready인가
381 | 반복 Restart가 없는가
382 | 실제 Infra 배치가 맞는가
383 | Service·Endpoint가 연결되는가
384 | Critical Event가 없는가
385 | ```
386 | 
387 | > 정확한 Component 이름과 Replica 수는 현재 Bundle을 기준으로 합니다. 과거 Host·Member의 Pod 수를 신규 Member 기대값으로 사용하지 않습니다.
388 | 
389 | ---
390 | 
391 | # 11. Installer 완료와 Member 기능 완료를 분리한다
392 | 
393 | ```text
394 | Installer Task 성공
395 | → 설치 자동화 완료
396 | ```
397 | 
398 | 하지만 최종 Member 자체 성공은 다음을 추가로 요구한다.
399 | 
400 | ```text
401 | Console·API
402 | Storage PVC·Mount
403 | External Monitoring
404 | clusterRole=member
405 | Platform Workload 배치
406 | Ingress·Network
407 | Critical Event 없음
408 | ```
409 | 
410 | 즉:
411 | 
412 | ```text
413 | INSTALLER PASS
414 | ≠ MEMBER SELF PASS
415 | ```
416 | 
417 | ---
418 | 
419 | # 12. Member 자체 Pre-Join 검증을 다시 묶는다
420 | 
421 | Host Join 전에 Member는 독립적으로 정상이어야 한다.
422 | 
423 | ## 12.1 Kubernetes
424 | 
425 | ```text
426 | 9/1 KUBERNETES BASE PASS 유지
427 | API·Node·CNI·DNS·Ingress Critical Error 없음
428 | ```
429 | 
430 | ## 12.2 Storage
431 | 
432 | ```text
433 | 9/2 STORAGE PASS 유지
434 | KubeSphere·Monitoring PVC Mount 정상
435 | ```
436 | 
437 | ## 12.3 Monitoring
438 | 
439 | ```text
440 | MONITORING PASS
441 | External ETCD Target UP
442 | Grafana Query 정상
443 | ```
444 | 
445 | ## 12.4 KubeSphere
446 | 
447 | ```text
448 | Installer 핵심 Task 성공
449 | Console·API 정상
450 | clusterRole=member
451 | External Monitoring 실제 사용
452 | Platform Workload 배치 정상
453 | ```
454 | 
455 | ## 12.5 Identity·Network
456 | 
457 | ```text
458 | Cluster Name·Stage
459 | VIP-A·VIP-B
460 | Domain
461 | Host Join에 필요한 DNS·Network·TLS 전제
462 | ```
463 | 
464 | > Member 자체 장애를 Host Join으로 덮지 않습니다.
465 | 
466 | ---
467 | 
468 | # 13. MEMBER SELF PASS를 판정한다
469 | 
470 | ## 13.1 MEMBER SELF PASS
471 | 
472 | ```text
473 | KUBERNETES BASE PASS 유지
474 | + STORAGE PASS 유지
475 | + MONITORING PASS
476 | + installer 핵심 Task 성공
477 | + KubeSphere 주요 Workload Ready
478 | + Console·API 실제 접근 정상
479 | + clusterRole=member
480 | + External Monitoring 실제 기능 정상
481 | + KubeSphere PVC·Mount 정상
482 | + Infra 배치 정책 정상
483 | + Registry·Image 오류 없음
484 | + Critical Event 없음
485 | + Join에 필요한 Network·Identity 전제 확인
486 | ```
487 | 
488 | > 이 판정이 Host Join의 입력입니다.
489 | 
490 | ## 13.2 BLOCKED
491 | 
492 | ```text
493 | Kubernetes·Storage·Monitoring 기존 Gate 회귀
494 | Installer 핵심 Task 실패
495 | KubeSphere PVC Mount 실패
496 | Console·API 핵심 기능 실패
497 | clusterRole 오류
498 | External Monitoring 연결 실패
499 | Platform Workload 핵심 Pod 비정상
500 | 잘못된 Cluster Identity·Domain·Registry 혼입
501 | Host Join 전제 Network·DNS·TLS 미확정
502 | ```
503 | 
504 | > BLOCKED Member를 Host에 Join해 상태를 더 복잡하게 만들지 않습니다.
505 | 
506 | ---
507 | 
508 | # 14. Host Join 블록으로 넘길 증거
509 | 
510 | ```text
511 | Cluster Name·Stage·Context
512 | MEMBER SELF PASS / BLOCKED
513 | Kubernetes·Storage·Monitoring 기존 Gate 결과
514 | Installer Log·핵심 Task 결과
515 | KubeSphere Console·API
516 | clusterRole=member 증거
517 | External Monitoring Endpoint·실제 기능
518 | KubeSphere PVC·Mount 결과
519 | Platform Workload·실제 Infra 배치
520 | Member VIP-A·VIP-B·Domain
521 | Join에 필요한 보호값 종류·전달 절차
522 | 미해결 Member 자체 항목
523 | ```
524 | 
525 | > Join 정보의 원문은 넘기지 않고 승인된 전달 경로와 값의 종류만 문서화합니다.
526 | 
527 | ---
528 | 
529 | # 15. 마무리 — Member KubeSphere 완료를 한 문장으로 다시 말한다
530 | 
531 | > Member KubeSphere 설치는 `ks-installer` Pod를 띄우는 일이 아닙니다.
532 | >
533 | > 검증된 Storage와 Monitoring, Registry와 ETCD를 현재 Member 실제값으로 연결하고, Installer 내부 Task가 성공하며, Platform Workload가 승인된 Infra Node에 배치되고, Console·API와 external Monitoring이 실제로 기능하며, `clusterRole=member`가 의도대로 적용되어야 합니다.
534 | >
535 | > **결국 Host Join 전에 신규 Member는 Host 도움 없이도 Kubernetes·Storage·Monitoring·KubeSphere 자체 기능이 정상인 독립된 Member여야 합니다.**
536 | 
537 | ---
538 | 
539 | # 16. 마지막 Teach-back
540 | 
541 | 1. `kubesphere-installer.yaml`과 ClusterConfiguration은 어떤 역할 차이가 있는가?
542 | 2. ks-installer Pod Running과 Installer 내부 Task 성공은 왜 다른가?
543 | 3. Host Manifest를 복사해 `clusterRole`만 바꾸면 안 되는 이유는 무엇인가?
544 | 4. Monitoring Task 실패 시 9월 3일 첫 블록 증거를 먼저 대조해야 하는 이유는 무엇인가?
545 | 5. Platform Workload가 Running이어도 실제 Infra 배치를 확인해야 하는 이유는 무엇인가?
546 | 6. 9월 2일 Test PVC 성공이 KubeSphere PVC 성공을 보장하지 않는 이유는 무엇인가?
547 | 7. External Monitoring Endpoint가 설정됐다는 것과 KubeSphere가 실제 Metric을 사용하는 것은 무엇이 다른가?
548 | 8. Console이 열려도 Member Self PASS가 아닌 경우는 무엇인가?
549 | 9. Host Join 전에 Member 자체를 독립적으로 검증해야 하는 이유는 무엇인가?
550 | 10. 어떤 상태가 남으면 Host Join을 BLOCKED해야 하는가?
551 | 
552 | ---
553 | 
554 | # 기준 문서 바로가기
555 | 
556 | - [[출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수|2026-09-03 Member 구축 4일차 기준]]
557 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
558 | - [[30. 구축 및 전환/Member 클러스터/05.2.2 Install KubeSphere on Member Cluster|Member KubeSphere 설치]]
559 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
560 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오후/01. 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본.md

Bytes: 14362
SHA-256: 7ac6da66b18b960a481abfe99f1c2e8187c8995d3b03e28aa5b02a271613126e
Lines: 1-523 of 523

```markdown
  1 | ---
  2 | title: "기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-03 Xi'an 신규 Member 구축 4일차 오후 - 기존 Host Join과 Multi-Cluster 실제 기능 검증"
  6 | created: "2026-08-28"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 오전 `MEMBER SELF PASS`를 입력으로 받아 **기존 Xi'an Host Cluster가 신규 Member를 실제로 관리·관측할 수 있는 Multi-Cluster 연결이 성립했는지 증명하는 법**을 가르친다. 기존 Host를 재설치하거나 공통 설정을 불필요하게 바꾸지 않는다. Join의 정확한 UI·Manifest·보호값 처리 절차는 현재 Host/Member Runbook을 따른다.
 14 | 
 15 | ## 0. 오전에서 이어받는 것
 16 | 
 17 | ```text
 18 | Cluster Name·Stage·Context
 19 | MEMBER SELF PASS / BLOCKED
 20 | KUBERNETES BASE PASS
 21 | STORAGE PASS
 22 | MONITORING PASS
 23 | KubeSphere Console·API 정상
 24 | clusterRole=member
 25 | External Monitoring 정상
 26 | Platform Workload 배치 정상
 27 | Member VIP-A·VIP-B·Domain
 28 | Join에 필요한 보호값 종류·전달 절차
 29 | ```
 30 | 
 31 | > `MEMBER SELF PASS`가 아니면 Join하지 않습니다. Member 자체 장애를 Host 연결 문제로 보이게 만들지 않습니다.
 32 | 
 33 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 34 | 
 35 | > Host Console에 Cluster 이름이 보이는 것만으로 Join 성공을 선언하지 않고, **기존 Host 자체 정상 → Join Identity·보호정보 → Agent·연결 Component → Host Console 상태 → Member Resource 조회 → Monitoring 관측 → 기존 Member 회귀 없음**을 독립 증거로 확인할 수 있어야 한다.
 36 | 
 37 | 오늘의 중심 질문:
 38 | 
 39 | > **Host가 신규 Member를 목록에 추가한 것이 아니라 실제로 관리·관측할 수 있으며, 기존 Multi-Cluster 환경에 회귀를 만들지 않았다는 것을 무엇으로 증명할 것인가?**
 40 | 
 41 | ---
 42 | 
 43 | # 1. 시작 — Join은 UI 목록 추가가 아니다
 44 | 
 45 | 정상 의미:
 46 | 
 47 | ```text
 48 | 신규 Member 자체 정상
 49 | + 기존 Host 자체 정상
 50 | + 현재 Member Identity로 Join
 51 | + Host↔Member Network·DNS·TLS·인증
 52 | + 연결 Agent·Component 정상
 53 | = Host가 Member를 실제로 관리·관측
 54 | ```
 55 | 
 56 | 반드시 구분한다.
 57 | 
 58 | ```text
 59 | Host Console에 Cluster 이름 표시
 60 | ≠ Multi-Cluster 기능 정상
 61 | 
 62 | Cluster Status 정상
 63 | ≠ Resource 조회·관리 정상
 64 | 
 65 | Resource 조회 가능
 66 | ≠ Monitoring 관측 정상
 67 | 
 68 | 신규 Member Join 성공
 69 | ≠ 기존 Member 영향 없음
 70 | ```
 71 | 
 72 | ---
 73 | 
 74 | # 2. Join 전에 기존 Host는 읽기 전용으로 정상 기준을 고정한다
 75 | 
 76 | > 이번 출장에서 기존 Host는 신규 구축 대상이 아닙니다. Join 전 기준 상태를 기록해 Join 후 회귀를 비교할 수 있게 합니다.
 77 | 
 78 | 확인할 최소 항목:
 79 | 
 80 | ```text
 81 | Host Cluster Identity
 82 | Host KubeSphere Console·API 접근
 83 | clusterRole=host
 84 | 기존 PRD·DEV Member 목록·Status
 85 | 기존 Member 주요 Resource 조회 가능
 86 | 기존 Multi-Cluster Component 상태
 87 | 신규 Member Name 중복 여부
 88 | Join 수행 권한·승인자
 89 | Host↔신규 Member Network·DNS 전제
 90 | ```
 91 | 
 92 | ## 2.1 기존 Host의 성공을 신규 Member 증거로 쓰지 않는다
 93 | 
 94 | ```text
 95 | 기존 PRD Member Status 정상
 96 | ≠ 신규 Member Join 가능
 97 | ```
 98 | 
 99 | 반대로:
100 | 
101 | ```text
102 | 기존 Host 자체 비정상
103 | ≠ 신규 Member Join 문제
104 | ```
105 | 
106 | > Join 전 Host 문제가 있으면 먼저 영향 범위를 분리합니다.
107 | 
108 | ---
109 | 
110 | # 3. Join Identity를 고정한다
111 | 
112 | ```text
113 | 신규 Member Cluster Name: ________________________________
114 | Stage: ___________________________________________________
115 | Member clusterRole: member
116 | Host Cluster Name: _______________________________________
117 | Host clusterRole: host
118 | Join 경로·방식: __________________________________________
119 | Join 승인자: _____________________________________________
120 | 실행 시각: _______________________________________________
121 | ```
122 | 
123 | 확인 규율:
124 | 
125 | ```text
126 | Cluster Name이 기존 Cluster와 중복되지 않음
127 | Stage·Tag가 현재 Member와 일치
128 | 과거 PRD·DEV Member 이름을 재사용하지 않음
129 | ```
130 | 
131 | > 이름이 잘못되면 나중에 Monitoring Label과 운영 대상 선택까지 혼동됩니다.
132 | 
133 | ---
134 | 
135 | # 4. 보호된 Join 정보는 값보다 전달 경계를 관리한다
136 | 
137 | 보호 대상 예:
138 | 
139 | ```text
140 | Join Secret
141 | JWT
142 | kubeconfig
143 | Token
144 | Private Key
145 | Password
146 | ```
147 | 
148 | 교육·증적에 기록할 수 있는 것:
149 | 
150 | ```text
151 | 값의 종류
152 | 발급·확인 시각
153 | 전달자·수신자 역할
154 | 승인된 전달 방식
155 | 사용 성공 여부
156 | 폐기·Rotation 필요 여부
157 | ```
158 | 
159 | 기록하지 않을 것:
160 | 
161 | ```text
162 | 실제 Secret Data
163 | Token·JWT 원문
164 | kubeconfig 원문
165 | Private Key
166 | Password
167 | ```
168 | 
169 | > 보호값을 화면 공유·채팅·Shell History에 남기지 않습니다.
170 | 
171 | ## 4.1 값 이름이 같아도 현재 Member 값인지 별도 확인한다
172 | 
173 | ```text
174 | Secret 이름 동일
175 | ≠ 현재 Member Join 정보
176 | ```
177 | 
178 | > 과거 Member의 Join 값을 재사용하지 않습니다.
179 | 
180 | ---
181 | 
182 | # 5. Join 전 Network는 양방향 필요한 경로를 확인한다
183 | 
184 | Multi-Cluster 연결에는 환경에 따라 여러 방향 통신이 필요할 수 있다.
185 | 
186 | 확인 질문:
187 | 
188 | ```text
189 | Host가 Member API·필요 Endpoint에 접근 가능한가
190 | Member가 Host 연결 Endpoint에 접근 가능한가
191 | DNS가 양쪽에서 승인 주소를 반환하는가
192 | TLS Certificate가 현재 FQDN과 맞는가
193 | 필요 Port·Firewall 정책이 승인됐는가
194 | Proxy 영향이 없는가
195 | ```
196 | 
197 | 구분:
198 | 
199 | ```text
200 | Ping 또는 TCP 한 Port 성공
201 | ≠ Join 전체 통신 정상
202 | ```
203 | 
204 | > 실제 Join 방식이 사용하는 Endpoint·Port만 Runbook 기준으로 확인합니다. 필요하지 않은 방화벽을 넓히지 않습니다.
205 | 
206 | ---
207 | 
208 | # 6. Join 적용 뒤 먼저 연결 Component를 본다
209 | 
210 | 실제 Join 방식에 따라 Member Agent와 Host 측 Multi-Cluster Component가 생성·갱신될 수 있다.
211 | 
212 | 확인:
213 | 
214 | ```text
215 | Member 측 연결 Agent Pod·Deployment
216 | Host 측 관련 Component
217 | Ready·Restart
218 | Event
219 | Log의 최초 오류
220 | 현재 Member Identity
221 | ```
222 | 
223 | 구분:
224 | 
225 | ```text
226 | Agent Pod Running
227 | ≠ Registration 완료
228 | 
229 | Registration 완료
230 | ≠ Host에서 Member Resource 조회 가능
231 | ```
232 | 
233 | ## 6.1 Agent가 Pending이면
234 | 
235 | ```text
236 | Node Selector·Taint
237 | PVC 필요 여부
238 | Image Pull
239 | Resource Request
240 | Scheduler Event
241 | ```
242 | 
243 | ## 6.2 Agent가 Running이지만 연결 실패면
244 | 
245 | ```text
246 | Host Endpoint
247 | DNS·Network·TLS
248 | 보호된 Join 정보 유효성
249 | Cluster Identity
250 | Log의 최초 연결 오류
251 | ```
252 | 
253 | > Member KubeSphere 전체를 재설치하지 않습니다.
254 | 
255 | ---
256 | 
257 | # 7. Host Console 등록 상태는 첫 번째 UI 증거일 뿐이다
258 | 
259 | 확인:
260 | 
261 | ```text
262 | 신규 Member 이름이 한 번만 표시
263 | Stage·Identity 정확
264 | Status 정상 또는 현재 Runbook의 기대 상태
265 | 등록 시각과 Join 시각 연결
266 | ```
267 | 
268 | 하지만:
269 | 
270 | ```text
271 | 목록 표시
272 | ≠ Node·Namespace·Workload 조회 정상
273 | ```
274 | 
275 | > 다음 실제 관리 경로를 확인해야 합니다.
276 | 
277 | ---
278 | 
279 | # 8. Host에서 Member Resource를 실제로 조회한다
280 | 
281 | 검증할 최소 Resource:
282 | 
283 | ```text
284 | Node 수·Role
285 | Namespace·Project
286 | 대표 Workload 상태
287 | 필요한 KubeSphere Resource
288 | ```
289 | 
290 | 대조:
291 | 
292 | ```text
293 | Host에서 본 Member Node 수·Role
294 | ↔ Member 자체 kubectl 결과
295 | ```
296 | 
297 | ```text
298 | Host에서 본 Workload
299 | ↔ Member 자체 KubeSphere·kubectl 결과
300 | ```
301 | 
302 | > Host에서 다른 Member를 선택한 결과를 신규 Member 증거로 사용하지 않습니다.
303 | 
304 | ## 8.1 조회 성공과 관리 권한을 구분한다
305 | 
306 | ```text
307 | 조회 가능
308 | ≠ 모든 변경 권한 정상
309 | ```
310 | 
311 | 현재 인수 범위에서 필요한 승인된 관리 기능만 확인한다. 불필요한 운영 Resource 변경을 Test로 만들지 않는다.
312 | 
313 | ---
314 | 
315 | # 9. Host에서 Member Monitoring을 실제로 관측한다
316 | 
317 | Monitoring은 오늘 오전 이미 Member 자체에서 `MONITORING PASS`를 받았다.
318 | 
319 | Host 측에서 추가로 확인할 것은:
320 | 
321 | ```text
322 | 현재 신규 Member를 선택했을 때 Metric이 보이는가
323 | Cluster Label이 신규 Member인가
324 | Node·Workload Metric이 Member 실제 상태와 대략 일치하는가
325 | 최근 데이터가 있는가
326 | 기존 PRD·DEV Metric과 섞이지 않는가
327 | ```
328 | 
329 | 구분:
330 | 
331 | ```text
332 | Host에서 Resource 조회 성공
333 | ≠ Monitoring 관측 성공
334 | ```
335 | 
336 | ## 9.1 Monitoring이 안 보이면 Storage부터 재설치하지 않는다
337 | 
338 | 첫 분기:
339 | 
340 | ```text
341 | Member 자체 Prometheus Query 정상인가
342 | Host가 참조하는 Metric Endpoint는 무엇인가
343 | Cluster External Label이 맞는가
344 | Multi-Cluster Monitoring Component가 정상인가
345 | ```
346 | 
347 | > Member 자체 Monitoring PASS가 유지되면 Host↔Monitoring 통합 경계를 먼저 봅니다.
348 | 
349 | ---
350 | 
351 | # 10. Host와 Member 양쪽 Console·API를 구분한다
352 | 
353 | ```text
354 | Member 자체 Console·API
355 | → Member Platform 자체 정상
356 | 
357 | Host Console에서 Member 관리
358 | → Multi-Cluster 연결 정상
359 | ```
360 | 
361 | 둘 다 필요하다.
362 | 
363 | ```text
364 | Host에서 Member 보임
365 | ≠ Member 자체 KubeSphere 정상
366 | 
367 | Member 자체 Console 정상
368 | ≠ Host Join 정상
369 | ```
370 | 
371 | > 오전 `MEMBER SELF PASS` 증거와 오후 Host 결과를 같이 인수 자료에 남깁니다.
372 | 
373 | ---
374 | 
375 | # 11. 기존 Member 회귀를 반드시 확인한다
376 | 
377 | > Host Join은 기존 Host의 Multi-Cluster 공통 영역과 연결됩니다. 신규 Member가 정상이어도 기존 PRD·DEV Member에 영향을 주면 최종 성공이 아닙니다.
378 | 
379 | Join 전후 대조:
380 | 
381 | ```text
382 | 기존 Member 목록·Status
383 | 기존 Member Resource 조회
384 | 기존 Member Monitoring 관측
385 | Host 공통 Component Restart·Error
386 | ```
387 | 
388 | 구분:
389 | 
390 | ```text
391 | 신규 Member 정상
392 | ≠ 기존 Member 회귀 없음
393 | ```
394 | 
395 | ## 11.1 기존 Member 영향이 보이면
396 | 
397 | 즉시 추가 Join·Host 공통 변경을 멈춘다.
398 | 
399 | 확인:
400 | 
401 | ```text
402 | Join 과정에서 Host 공통 Config 변경이 있었는가
403 | Multi-Cluster Component가 Restart·Error 상태인가
404 | 기존 Member 인증·Endpoint에 공통 영향이 있는가
405 | ```
406 | 
407 | > 기존 Member까지 동시에 수정하지 않습니다. 신규 Join과 영향 관계를 먼저 고정합니다.
408 | 
409 | ---
410 | 
411 | # 12. Join 실패는 마지막 성공으로 분기한다
412 | 
413 | | 증상 | 첫 확인 |
414 | |---|---|
415 | | Host Console에 신규 Member 없음 | Join 요청·Identity·권한·보호값·Host Component |
416 | | 이름은 보이나 Status 비정상 | Member 자체 상태·Agent·Host→Member Network·TLS |
417 | | Resource 조회 실패 | 권한·API·Agent·Cluster 선택 |
418 | | Resource는 보이나 Monitoring 없음 | Member Monitoring·Endpoint·Label·통합 Component |
419 | | 기존 Member 영향 | Host 공통 Component·Config 변경·회귀 범위 |
420 | 
421 | > `Join 실패` 하나로 묶지 않고 어디까지 성공했는지 먼저 말합니다.
422 | 
423 | ---
424 | 
425 | # 13. MULTI-CLUSTER PASS를 판정한다
426 | 
427 | ## 13.1 MULTI-CLUSTER PASS
428 | 
429 | ```text
430 | MEMBER SELF PASS 유지
431 | + 기존 Host 자체 정상 기준 확인
432 | + Host clusterRole=host
433 | + 신규 Member Identity·Name 중복 없음
434 | + 보호값 안전한 전달·사용
435 | + 필요한 Host↔Member Network·DNS·TLS 정상
436 | + Member Agent·연결 Component 정상
437 | + Host Console 등록·Status 정상
438 | + Host에서 Member Node·Namespace·Workload 조회 가능
439 | + 필요한 관리 권한 경계 정상
440 | + Host에서 Member Monitoring 관측 가능
441 | + Metric Cluster Label이 현재 Member
442 | + 기존 PRD·DEV Member 회귀 없음
443 | + Host 공통 Component Critical Error 없음
444 | ```
445 | 
446 | > 이 상태가 최종 인수 블록의 입력입니다.
447 | 
448 | ## 13.2 BLOCKED
449 | 
450 | ```text
451 | MEMBER SELF PASS 회귀
452 | Host 자체 핵심 장애
453 | Join Identity·보호값 유효성 미확정
454 | 필요 Network·DNS·TLS 실패
455 | Agent·Registration 실패
456 | Host Console Status 비정상
457 | Member Resource 조회 불가
458 | Member Monitoring 관측 실패 원인 미확정
459 | 기존 Member 회귀 발생
460 | 보호된 값 노출·통제 문제
461 | ```
462 | 
463 | > 최종 인수에서 PASS로 숨기지 않습니다.
464 | 
465 | ---
466 | 
467 | # 14. 최종 인수 블록으로 넘길 증거
468 | 
469 | ```text
470 | Member Cluster Name·Stage
471 | MEMBER SELF PASS
472 | Host Cluster Identity·Role
473 | Join 방식·실행 시각·승인자
474 | 보호값 종류·안전한 전달 결과
475 | Member Agent·연결 Component 상태
476 | Host Console 신규 Member Status
477 | Host에서 Member Resource 조회 결과
478 | Host에서 Member Monitoring 관측 결과
479 | Cluster Label 대조
480 | 기존 Member Join 전·후 회귀 결과
481 | Host 공통 Component 상태
482 | MULTI-CLUSTER PASS / BLOCKED
483 | 미해결 Join·회귀 항목
484 | ```
485 | 
486 | > 최종 인수는 이 증거를 8월 31일부터의 전체 Gate와 연결합니다.
487 | 
488 | ---
489 | 
490 | # 15. 마무리 — Host Join 완료를 한 문장으로 다시 말한다
491 | 
492 | > Host Join은 Cluster 이름을 Console 목록에 추가하는 작업이 아닙니다.
493 | >
494 | > 정상인 Member와 정상인 Host가 현재 Member Identity와 보호된 연결정보로 통신하고, 연결 Agent와 Component가 정상이며, Host가 Member의 Resource를 실제로 조회·관리하고 Monitoring을 관측할 수 있어야 합니다.
495 | >
496 | > 동시에 기존 PRD·DEV Member와 Host 공통 기능에 회귀가 없어야 합니다.
497 | >
498 | > **결국 Multi-Cluster PASS는 신규 Member가 기존 Xi'an Host의 운영 가능한 구성원으로 실제 연결됐고, 그 연결이 기존 환경을 깨뜨리지 않았다는 증거입니다.**
499 | 
500 | ---
501 | 
502 | # 16. 마지막 Teach-back
503 | 
504 | 1. Host Console에 Cluster 이름이 보이는 것과 Multi-Cluster 정상은 무엇이 다른가?
505 | 2. Join 전에 기존 Host 정상 기준을 읽기 전용으로 기록해야 하는 이유는 무엇인가?
506 | 3. 보호된 Join 값에서 문서화할 수 있는 정보와 기록하면 안 되는 정보는 무엇인가?
507 | 4. Agent Pod Running과 Registration 완료는 왜 다른가?
508 | 5. Host에서 Member Resource 조회와 Monitoring 관측을 별도로 확인해야 하는 이유는 무엇인가?
509 | 6. Member 자체 Console 정상과 Host Join 정상은 어떻게 다른가?
510 | 7. 기존 Member 회귀 확인이 신규 Member Join 검증의 일부인 이유는 무엇인가?
511 | 8. Resource는 보이지만 Monitoring이 없을 때 어느 경계부터 확인해야 하는가?
512 | 9. 기존 Member까지 이상해지면 왜 추가 변경을 멈춰야 하는가?
513 | 10. `MULTI-CLUSTER PASS`가 증명하는 범위는 어디까지인가?
514 | 
515 | ---
516 | 
517 | # 기준 문서 바로가기
518 | 
519 | - [[출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수|2026-09-03 Member 구축 4일차 기준]]
520 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
521 | - [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
522 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
523 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/20. 교육/2026-09-03/오후/02. 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본.md

Bytes: 14497
SHA-256: c91dbacd3ff3fcaa6fea3e57847f33387f90467f771588b5d80e2592c87dd59d
Lines: 1-458 of 458

```markdown
  1 | ---
  2 | title: "전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본"
  3 | status: current
  4 | doc_type: instructor-script
  5 | scope: "2026-09-03 Xi'an 신규 Member 구축 4일차 오후 - 8월 31일~9월 3일 전체 구축 최종 인수"
  6 | created: "2026-08-28"
  7 | updated: "2026-08-28"
  8 | ---
  9 | 
 10 | # 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본
 11 | 
 12 | > [!important] 이 대본의 역할
 13 | > 이 문서는 `MULTI-CLUSTER PASS`까지의 결과를 받아 **8월 31일부터 9월 3일까지 구축한 신규 Member를 기능별 증거로 최종 인수하고, 남은 항목을 PASS·PARTIAL·BLOCKED로 투명하게 판정하는 법**을 가르친다. 이 문서에서는 새로운 기술 변경을 시작하지 않는다. 이미 수행한 구축의 성공 범위, 회귀, 증적, 보호된 값 정리와 현지 인계를 닫는다.
 14 | 
 15 | ## 0. 앞 블록에서 이어받는 것
 16 | 
 17 | ```text
 18 | 8/31 GO
 19 | 9/1 KUBERNETES BASE PASS
 20 | 9/2 STORAGE PASS
 21 | 9/3 MONITORING PASS
 22 | 9/3 MEMBER SELF PASS
 23 | 9/3 MULTI-CLUSTER PASS
 24 | 각 Gate의 증적 위치
 25 | 미해결·외부 확인 항목
 26 | 기존 Member 회귀 결과
 27 | 보호된 값 사용·정리 상태
 28 | ```
 29 | 
 30 | > 앞 Gate가 BLOCKED인데 최종 문서만 PASS로 만들지 않습니다.
 31 | 
 32 | ## 0.1 이 블록이 끝난 뒤 수강생이 할 수 있어야 하는 것
 33 | 
 34 | > 전체 구축을 명령 실행 목록이 아니라 **현실·자동화 입력·Kubernetes 기능·Storage 사용·Monitoring·Member Platform·Host Join·기존 환경 회귀**의 증거 사슬로 복원하고, 잔여 항목의 실제 영향을 기준으로 최종 인수 상태를 판정할 수 있어야 한다.
 35 | 
 36 | 오늘의 중심 질문:
 37 | 
 38 | > **어떤 기능 증거와 잔여 항목 기록이 있어야 신규 Member가 Xi'an Multi-Cluster의 운영 가능한 구성원으로 인수됐다고 말할 수 있는가?**
 39 | 
 40 | ---
 41 | 
 42 | # 1. 시작 — 최종 인수는 마지막 화면 캡처가 아니다
 43 | 
 44 | 전체 흐름을 한 번 복원한다.
 45 | 
 46 | ```text
 47 | 8/31
 48 | 실제 VM·LB·Disk 확인
 49 | → Bastion·Node Pre-setting
 50 | → 실제값을 Inventory로 표현
 51 | → 실행 전 GO
 52 | 
 53 | 9/1
 54 | Kubespray 실행
 55 | → API·Node·Control Plane
 56 | → ETCD·Runtime·CNI·DNS·Ingress
 57 | → KUBERNETES BASE PASS
 58 | 
 59 | 9/2
 60 | Snapshotter·Trident·Backend·StorageClass
 61 | → PVC·PV
 62 | → Pod Mount
 63 | → Write·Read·Cleanup
 64 | → STORAGE PASS
 65 | 
 66 | 9/3 오전
 67 | Monitoring
 68 | → KubeSphere Member 자체 기능
 69 | → MEMBER SELF PASS
 70 | 
 71 | 9/3 오후
 72 | 기존 Host Join
 73 | → Multi-Cluster 관리·관측
 74 | → 기존 Member 회귀 확인
 75 | → MULTI-CLUSTER PASS
 76 | ```
 77 | 
 78 | > 최종 인수는 이 연결이 실제 증거로 이어지는지 확인하는 작업입니다.
 79 | 
 80 | ---
 81 | 
 82 | # 2. 인수 매트릭스는 기능과 증거를 연결한다
 83 | 
 84 | | 영역 | 반드시 증명할 기능 | 최소 증거 |
 85 | |---|---|---|
 86 | | 환경·VM | 승인 Role·Hostname·IP·Disk | 8/31 실제값 표 |
 87 | | Bastion | 올바른 설치 기준점 | DNS·sudo·Repo·Bundle·SSH 기능 결과 |
 88 | | Inventory | 현실을 정확히 표현 | Host·Group·VIP·CIDR·Registry·Version 대조 |
 89 | | Kubespray | 미해결 자동화 오류 없이 적용 | Log·Return Code·PLAY RECAP |
 90 | | Kubernetes API | 승인 VIP-A Control Path | Context·readyz·전역값 |
 91 | | Node·Control Plane | 실제 Cluster 기본 제어 기능 | Node Role·Ready·Component 상태 |
 92 | | ETCD·Runtime·CNI·DNS·Ingress | 실제 Application 기본 경로 | health·Test Pod·DNS·VIP-B |
 93 | | Storage | 실제 Persistent Storage 사용 | Backend·SC·PVC·Mount·Write/Read·Cleanup |
 94 | | Monitoring | 현재 Member Metric 관측 | Target UP·Query·Datasource·Ingress |
 95 | | Member KubeSphere | 실제 Member Platform | Installer Task·Console·API·member Role·배치 |
 96 | | Host Join | Multi-Cluster 관리·관측 | Agent·Host Status·Resource·Monitoring |
 97 | | 회귀 | 기존 환경 영향 없음 | Join 전후 기존 Member 비교 |
 98 | | 보안 | 보호값 통제 | 원문 미포함·임시 파일 정리·전달 기록 |
 99 | 
100 | > 표의 빈칸을 “정상으로 보임”으로 채우지 않습니다. 실제 증적 위치를 적습니다.
101 | 
102 | ---
103 | 
104 | # 3. 하나의 성공으로 다른 영역을 대신하지 않는다
105 | 
106 | 최종 인수에서 가장 위험한 과잉 판정:
107 | 
108 | ```text
109 | Kubespray Return Code 0
110 | ≠ Kubernetes 기능 전체 정상
111 | 
112 | Node Ready
113 | ≠ Storage·Monitoring 정상
114 | 
115 | PVC Bound
116 | ≠ 실제 Write·Read 정상
117 | 
118 | Prometheus Pod Running
119 | ≠ Target UP·Query 정상
120 | 
121 | KubeSphere Console 열림
122 | ≠ Member Platform 전체 정상
123 | 
124 | Host Console에 Member 표시
125 | ≠ Multi-Cluster 관리·관측 정상
126 | ```
127 | 
128 | > 각 Gate를 그대로 유지하는 이유가 여기에 있습니다.
129 | 
130 | ---
131 | 
132 | # 4. 실제값과 최종 운영 Identity를 다시 한 장에 고정한다
133 | 
134 | ```text
135 | Member Cluster Name: ____________________________________
136 | Stage: ___________________________________________________
137 | VIP-A: ___________________________________________________
138 | VIP-B: ___________________________________________________
139 | Domain: __________________________________________________
140 | Kubernetes Version: ______________________________________
141 | Pod CIDR: ________________________________________________
142 | Service CIDR: ____________________________________________
143 | StorageClass: ____________________________________________
144 | Monitoring Namespace: ___________________________________
145 | Monitoring FQDN: _________________________________________
146 | KubeSphere FQDN: _________________________________________
147 | clusterRole: member
148 | 기존 Host Cluster: _______________________________________
149 | Host에서 보이는 Member 이름: ____________________________
150 | ```
151 | 
152 | > 인수 문서의 Identity가 실제 Cluster·Host Console·Monitoring Label과 같아야 합니다.
153 | 
154 | ---
155 | 
156 | # 5. 증적은 ‘원본 출력’과 ‘판단 요약’을 분리한다
157 | 
158 | 권장 구조:
159 | 
160 | ```text
161 | 원본 실행·조회 증적
162 | → 당시 실제 출력·Log·Screenshot
163 | 
164 | 판단 요약
165 | → 어떤 질문에 답했고 무엇을 증명했는지
166 | ```
167 | 
168 | > 요약 문서만 남기면 나중에 판정 근거를 다시 확인할 수 없고, 원본 Log만 남기면 무엇을 보고 PASS했는지 알기 어렵습니다.
169 | 
170 | ## 5.1 증적 파일 규칙
171 | 
172 | ```text
173 | 날짜
174 | 대상 Cluster
175 | 영역
176 | 검증 시각
177 | 현재 실행임을 식별할 Dynamic Resource 정보
178 | ```
179 | 
180 | Screenshot은 민감정보를 Masking한다.
181 | 
182 | 참조·과거 출력과 실제 신규 Member 실행 증거를 구분한다.
183 | 
184 | ---
185 | 
186 | # 6. 보호된 값은 최종 증적에 넣지 않는다
187 | 
188 | 포함 금지:
189 | 
190 | ```text
191 | Password
192 | Token
193 | JWT
194 | Secret Data
195 | Private Key
196 | kubeconfig 원문
197 | Registry Credential
198 | ETCD Client Key
199 | 인증서 Private Key
200 | Join 보호값 원문
201 | ```
202 | 
203 | 대신 기록할 수 있는 것:
204 | 
205 | ```text
206 | 값의 종류
207 | 사용 목적
208 | 발급·사용 시각
209 | 전달자·수신자 역할
210 | 승인된 관리체계
211 | 사용 성공 여부
212 | 폐기·Rotation 필요 여부
213 | ```
214 | 
215 | ## 6.1 임시 파일·Clipboard·Shell History 정리
216 | 
217 | > 보호값을 사용했다면 인수 전에 임시 파일, Local Download, Clipboard, 불필요한 Shell History 노출 여부를 현재 운영 기준에 따라 정리합니다.
218 | 
219 | ```text
220 | 값을 성공적으로 사용함
221 | ≠ 보호된 복사본 정리 완료
222 | ```
223 | 
224 | ---
225 | 
226 | # 7. 회귀는 최종 성공의 일부다
227 | 
228 | 신규 Member만 정상이라고 끝내지 않는다.
229 | 
230 | 확인:
231 | 
232 | ```text
233 | 기존 Host Console·API
234 | 기존 PRD·DEV Member Status
235 | 기존 Member Resource 조회
236 | 기존 Member Monitoring 관측
237 | Host 공통 Component 상태
238 | ```
239 | 
240 | Join 전과 Join 후 차이를 기록한다.
241 | 
242 | ```text
243 | 기존 Member 영향 없음
244 | = 최종 인수의 독립 증거
245 | ```
246 | 
247 | > 기존 환경에 영향이 생겼다면 신규 Member 자체가 정상이어도 최종 PASS가 아닙니다.
248 | 
249 | ---
250 | 
251 | # 8. 잔여 항목은 ‘질문 목록’이 아니라 영향으로 분류한다
252 | 
253 | 잔여 항목 표:
254 | 
255 | | 항목 | 마지막 성공 | 최초 실패·미확인 | 기능 영향 | 다음 확인 | 담당 영역 | 기한 |
256 | |---|---|---|---|---|---|---|
257 | |  |  |  |  |  |  |  |
258 | 
259 | 분류:
260 | 
261 | ```text
262 | 비차단 잔여
263 | → 핵심 운영 기능은 정상이고 인수 가능
264 | 
265 | 차단 잔여
266 | → 핵심 기능 또는 안전한 운영을 막음
267 | 
268 | 외부 확인
269 | → 담당 영역의 확인 없이는 판정 불가
270 | ```
271 | 
272 | > “Q&A 남음”처럼 모호하게 적지 않습니다. 무엇이 아직 증명되지 않았는지 적습니다.
273 | 
274 | ---
275 | 
276 | # 9. 최종 판정은 PASS / PARTIAL / BLOCKED 세 상태만 사용한다
277 | 
278 | ## 9.1 PASS
279 | 
280 | ```text
281 | 모든 핵심 Gate PASS
282 | + 신규 Member 핵심 기능 정상
283 | + Multi-Cluster 관리·관측 정상
284 | + 기존 환경 회귀 없음
285 | + 보호값 통제·정리 완료
286 | + 잔여는 기능에 영향 없는 문서·부가 항목뿐
287 | + 담당자 인계 완료
288 | ```
289 | 
290 | ## 9.2 PARTIAL
291 | 
292 | PARTIAL은 중간 날짜 Gate에서 사용하지 않고 최종 인수에서만 사용한다.
293 | 
294 | 조건:
295 | 
296 | ```text
297 | 핵심 운영 기능은 정상
298 | + Multi-Cluster 핵심 관리·관측 가능
299 | + 기존 환경 회귀 없음
300 | + 보호값 문제 없음
301 | + 남은 항목이 비차단적
302 | + 영향·담당자·완료 기한이 명확
303 | ```
304 | 
305 | 예:
306 | 
307 | ```text
308 | 부가 Dashboard 추가
309 | 비핵심 문서 포맷 정리
310 | 비차단 Q&A·증적 파일명 정리
311 | ```
312 | 
313 | > 기능 미확정을 PARTIAL로 숨기지 않습니다.
314 | 
315 | ## 9.3 BLOCKED
316 | 
317 | 다음은 최종 완료 선언을 막는다.
318 | 
319 | ```text
320 | Kubernetes 기본 기능 비정상
321 | Storage Mount·Write/Read 실패
322 | Monitoring 핵심 Target·Query 실패
323 | External ETCD Target Down
324 | Member KubeSphere 핵심 Task·Console·API 실패
325 | clusterRole·Cluster Identity 오류
326 | Host Join 실패
327 | Host에서 Member Resource·Monitoring 관측 불가
328 | 기존 Member 회귀 발생
329 | 보호된 값 노출·통제 미확정
330 | 핵심 장애 원인·담당 경계 미확정
331 | ```
332 | 
333 | > 9월 4일은 기술 작업 Buffer가 아니므로 BLOCKED를 9월 4일에 강행해 숨기지 않습니다.
334 | 
335 | ---
336 | 
337 | # 10. 최종 인수 패킷을 만든다
338 | 
339 | 최소 포함 항목:
340 | 
341 | ```text
342 | 1. Member Identity·실제값 요약
343 | 2. 8/31 환경·Pre-setting·Inventory 증거
344 | 3. 9/1 Kubespray Log·Kubernetes 기능 증거
345 | 4. 9/2 Storage 공급·사용·Cleanup 증거
346 | 5. 9/3 Monitoring Target·Query·Ingress 증거
347 | 6. Member KubeSphere Task·Console·Role·배치 증거
348 | 7. Host Join·Multi-Cluster Resource·Monitoring 증거
349 | 8. 기존 Cluster 회귀 결과
350 | 9. 최종 PASS / PARTIAL / BLOCKED 판정
351 | 10. 잔여 항목·영향·담당자·기한
352 | 11. 보호된 값 미포함·정리 확인
353 | 12. 현지 담당자 인계 확인
354 | ```
355 | 
356 | > 실제 파일 위치를 인수 패킷에 적어 누구나 원본 증적까지 추적할 수 있어야 합니다.
357 | 
358 | ---
359 | 
360 | # 11. 현지 담당자에게 전달할 것은 명령 목록이 아니라 정상 기준이다
361 | 
362 | 현지 담당자가 인수 후 말할 수 있어야 할 것:
363 | 
364 | ```text
365 | 어디서 현재 Cluster Identity를 확인하는가
366 | Kubernetes 기본 PASS는 어떤 증거인가
367 | Storage 완료는 Bound가 아니라 무엇까지인가
368 | Monitoring 완료는 Target·Query에서 무엇을 보는가
369 | Member KubeSphere 정상은 어떤 기능 조합인가
370 | Host Join 정상은 목록 표시 외에 무엇을 보는가
371 | 장애 시 첫 단절을 어떻게 찾는가
372 | 어떤 원본 Runbook을 열어야 하는가
373 | 보호된 값은 어디에서 관리하는가
374 | ```
375 | 
376 | > 인수의 목적은 강사가 떠난 뒤에도 현지 운영자가 정상과 비정상을 구분할 수 있게 하는 것입니다.
377 | 
378 | ---
379 | 
380 | # 12. 9월 4일로 넘기는 것은 정리 업무다
381 | 
382 | 9월 4일 인계 항목:
383 | 
384 | ```text
385 | 최종 판정
386 | 증적 위치
387 | 잔여 비차단·차단 항목
388 | 담당자·기한
389 | Credential·임시 파일 정리 상태
390 | 장비·접근·출입 정리 항목
391 | 문서 위치
392 | ```
393 | 
394 | 9월 4일로 넘기지 않을 것:
395 | 
396 | ```text
397 | 미완료 핵심 Storage 구축
398 | 미완료 KubeSphere 핵심 설치
399 | 미완료 Host Join을 시간 맞추기 위해 강행
400 | 원인 미확정 Critical 장애의 추가 실험
401 | ```
402 | 
403 | > 일정 종료와 기술 완료를 혼동하지 않습니다.
404 | 
405 | ---
406 | 
407 | # 13. 최종 인수 회의에서 읽을 순서
408 | 
409 | ```text
410 | 1. 대상 Cluster Identity
411 | 2. 8/31 GO
412 | 3. 9/1 KUBERNETES BASE PASS
413 | 4. 9/2 STORAGE PASS
414 | 5. 9/3 MONITORING PASS
415 | 6. MEMBER SELF PASS
416 | 7. MULTI-CLUSTER PASS
417 | 8. 기존 환경 회귀 결과
418 | 9. 보호값 정리
419 | 10. 잔여 항목
420 | 11. 최종 판정
421 | ```
422 | 
423 | > 증적을 날짜별로 쌓기만 하지 않고 **각 날짜의 출력이 다음 날짜의 입력이 됐다는 연결**을 설명합니다.
424 | 
425 | ---
426 | 
427 | # 14. 마무리 — 이번 구축 전체를 한 문장으로 말한다
428 | 
429 | > 신규 Member 구축은 VM을 준비하고 Playbook을 실행하는 것으로 끝나지 않았습니다.
430 | >
431 | > 먼저 실제 환경을 확인해 자동화가 믿을 입력을 만들고, 그 입력으로 Kubernetes를 설치한 뒤 실제 API·Pod Network·DNS·Ingress 기능을 검증했습니다. 그 위에서 Storage를 실제 Mount·Write·Read하고, Monitoring이 현재 Member Metric을 수집·조회하도록 만들고, Member KubeSphere 자체 기능을 확인했습니다. 마지막으로 기존 Host에 Join하여 Multi-Cluster 관리·관측과 기존 환경 회귀를 확인했습니다.
432 | >
433 | > **결국 최종 인수는 ‘명령을 다 실행했다’가 아니라 ‘신규 Member가 독립적으로 정상이고 기존 Host의 운영 가능한 구성원으로 연결됐으며, 그 사실을 기능별 증거로 다시 설명할 수 있다’는 상태입니다.**
434 | 
435 | ---
436 | 
437 | # 15. 마지막 Teach-back
438 | 
439 | 1. 최종 인수에서 Kubespray Return Code 하나로 완료를 선언할 수 없는 이유는 무엇인가?
440 | 2. 8/31부터 9/3까지 각 Gate가 다음 날짜의 입력으로 어떻게 이어지는가?
441 | 3. 원본 출력과 판단 요약을 분리해서 남겨야 하는 이유는 무엇인가?
442 | 4. 최종 증적에 포함하면 안 되는 보호정보는 무엇인가?
443 | 5. 신규 Member가 정상이어도 기존 Member 회귀가 있으면 PASS가 아닌 이유는 무엇인가?
444 | 6. PARTIAL을 9/1·9/2 중간 Gate에서는 쓰지 않고 최종 인수에서만 쓰는 이유는 무엇인가?
445 | 7. 어떤 잔여 항목은 PARTIAL이 될 수 있고 어떤 항목은 반드시 BLOCKED인가?
446 | 8. 9월 4일을 기술 작업 Buffer로 사용하면 안 되는 이유는 무엇인가?
447 | 9. 현지 담당자에게 명령보다 정상 기준과 첫 단절 사고법을 인계해야 하는 이유는 무엇인가?
448 | 10. 이번 신규 Member 구축을 한 문장으로 설명한다면 무엇인가?
449 | 
450 | ---
451 | 
452 | # 기준 문서 바로가기
453 | 
454 | - [[출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수|2026-09-03 Member 구축 4일차 기준]]
455 | - [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
456 | - [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
457 | - [[출장/40. 현장 준비 및 기록/2026-09-04 현장 정리 및 철수|9월 4일 현장 정리 및 철수]]
458 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증.md

Bytes: 13935
SHA-256: 0ffd37f826af13a14fc06a8e129edb032ffcabc995f7f4b7fdf35053e244d761
Lines: 1-382 of 382

```markdown
  1 | ---
  2 | title: "2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증"
  3 | status: current
  4 | doc_type: build-note
  5 | scope: "2026-09-01 신규 Member Cluster Kubespray 실행, Kubernetes API·Node·System Pod·CNI·DNS 검증 및 실패 범위 판정"
  6 | created: "2026-08-15"
  7 | updated: "2026-08-28"
  8 | parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거]]"
  9 | ---
 10 | 
 11 | # 2026-09-01 Member 구축 2일차 - Kubespray 및 Kubernetes 검증
 12 | 
 13 | > [!important] 이 문서의 역할
 14 | > 이 문서는 9/1 신규 Member Kubernetes 구축일의 **현장 수행·판정 Source of Truth**이다. 8/31에 확정한 Inventory·환경값·Ansible 연결을 입력으로 Kubespray를 실행하고, 로그의 최초 실패 지점을 좁히며, 설치 후 API·Node·Control Plane·DNS·CNI·ETCD·Runtime이 실제로 성립했는지 여러 독립 증거로 판정한다. 강의의 설명 순서와 Teach-back은 아래 강사용 대본을 사용하고, 정확한 실행·검증 명령과 현장값은 이 문서와 원본 Runbook을 따른다.
 15 | >
 16 | > 날짜와 수행 범위는 [[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|8/21 최신 실행 일정]]을 최우선으로 하며, Playbook 종료 자체가 다음날 Storage 단계로 넘어가는 완료 조건은 아니다.
 17 | 
 18 | ### 9/1 강사용 대본
 19 | 
 20 | - [[출장/20. 교육/2026-09-01/오전/01. Kubespray 입력 최종 확인·실행·로그 판독 강사용 전체 대본|오전 - Kubespray 실행·로그 판독]]
 21 | - [[출장/20. 교육/2026-09-01/오후/01. Kubernetes API·전역 설정·Node·Control Plane 검증 강사용 전체 대본|오후 1 - Control Path 검증]]
 22 | - [[출장/20. 교육/2026-09-01/오후/02. External ETCD·Runtime·CNI·DNS·Ingress·9월 2일 Gate 강사용 전체 대본|오후 2 - Application 경로·9/2 Gate]]
 23 | 
 24 | > [!success] 9/1 종료 Gate
 25 | > 다음날 Storage로 넘어가는 판정은 강사용 대본의 `KUBERNETES BASE PASS / BLOCKED`를 사용한다. 핵심 Kubernetes 기반 오류가 남으면 `BLOCKED`로 판정하고 다음 단계로 넘기지 않는다.
 26 | 
 27 | ## 1. 9/1 확정 범위
 28 | 
 29 | - Kubespray Playbook 실행
 30 | - 진행 로그 확인
 31 | - 실패 지점 확인과 필요한 재실행
 32 | - Kubernetes API 확인
 33 | - Node 상태 확인
 34 | - System Pod 상태 확인
 35 | - 기본 네트워크 상태 검증
 36 | - 설치 과정의 오류와 설정값 리뷰
 37 | - 교육생이 직접 구축·검증
 38 | 
 39 | 이날의 핵심 질문은 다음이다.
 40 | 
 41 | > **Playbook이 끝났다는 것과 Kubernetes Cluster가 정상적으로 구축됐다는 것은 어떻게 다른가?**
 42 | 
 43 | ## 2. 머릿속에 있어야 할 흐름
 44 | 
 45 | ```text
 46 | 8/31에 검증한 Inventory·변수·Ansible 연결
 47 | → Kubespray cluster.yml 실행
 48 | → Ansible task / recap 확인
 49 | → 실패가 있으면 최초 실패 범위 확인
 50 | → API 접근 확인
 51 | → Node 등록·Role·Version 확인
 52 | → Control Plane / System Pod 확인
 53 | → CNI / CoreDNS / Ingress 기본 구성 확인
 54 | → 전역 변수와 실제 Cluster 상태 대조
 55 | → 9/2 Storage 설치로 이동
 56 | ```
 57 | 
 58 | ### 반드시 분리할 성공
 59 | 
 60 | ```text
 61 | ansible-playbook 종료 코드 0
 62 | ≠ 모든 설정값이 맞다
 63 | 
 64 | Node Ready
 65 | ≠ Kubernetes 핵심 컴포넌트 전체 검증 완료
 66 | 
 67 | System Pod Running
 68 | ≠ Storage·KubeSphere까지 DKS 구축 완료
 69 | ```
 70 | 
 71 | ## 3. Playbook 실행에서 이해해야 할 것
 72 | 
 73 | 근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
 74 | 
 75 | ### 실행 명령보다 먼저 설명할 것
 76 | 
 77 | - `cluster.yml`은 `hosts.yaml`과 변수 파일을 입력으로 사용한다.
 78 | - 같은 Playbook이라도 Inventory·CIDR·VIP·Registry가 다르면 다른 Cluster를 만든다.
 79 | - `--become`은 대상 노드에서 root 권한이 필요한 task를 수행하기 위한 것이다.
 80 | - 실패 시 명령을 무조건 처음부터 반복하는 것이 아니라 **어느 host의 어느 task에서 처음 실패했는지** 본다.
 81 | 
 82 | ### 로그에서 먼저 볼 것
 83 | 
 84 | ```text
 85 | 어느 Host인가?
 86 | 어느 Task인가?
 87 | FAILED / UNREACHABLE인가?
 88 | 모든 노드 공통인가, 특정 노드만인가?
 89 | Ansible recap에서 failed/unreachable이 몇 개인가?
 90 | ```
 91 | 
 92 | 원인을 바로 추정하기보다 **실패 위치를 먼저 고정**한다.
 93 | 
 94 | ## 4. 설치 후 전역 설정 대조
 95 | 
 96 | `03.md`의 배포 후 검증은 단순 Pod 조회보다 먼저 Cluster 전역 설정을 확인한다.
 97 | 
 98 | 내가 설명할 수 있어야 할 항목:
 99 | 
100 | - Control Plane Endpoint = VIP-A
101 | - Kubernetes version
102 | - Cluster DNS domain
103 | - Pod subnet
104 | - Service subnet
105 | - Node CIDR block size 등 설치 설계 관련 설정
106 | 
107 | 여기서 중요한 것은 숫자를 암기하는 것이 아니다.
108 | 
109 | > **8/31에 넣은 설계값이 9/1 만들어진 Cluster에 실제로 반영됐는지 확인하는 단계**라는 점을 설명할 수 있어야 한다.
110 | 
111 | ## 5. Kubernetes 핵심 컴포넌트 검증 구조
112 | 
113 | ### Control Plane
114 | 
115 | - kube-apiserver
116 | - kube-controller-manager
117 | - kube-scheduler
118 | 
119 | ### Node 공통
120 | 
121 | - kube-proxy
122 | - kubelet 상태
123 | 
124 | ### DNS
125 | 
126 | - CoreDNS
127 | 
128 | ### CNI
129 | 
130 | - calico-node
131 | - calico-controller
132 | - 환경에 따른 Typha 등
133 | 
134 | ### Ingress / Add-on
135 | 
136 | - ingress-nginx-controller
137 | - metrics-server
138 | - 기타 bundle이 설치하는 기본 addon
139 | 
140 | 정확한 Pod suffix를 외우지 않는다. **어떤 컴포넌트가 어느 역할 노드에 몇 개쯤 배치되어야 하는지**를 이해한다.
141 | 
142 | ## 6. Node 상태를 볼 때 알아야 할 것
143 | 
144 | `kubectl get nodes -o wide`에서 최소 다음을 읽을 수 있어야 한다.
145 | 
146 | ```text
147 | NAME
148 | STATUS
149 | ROLES
150 | VERSION
151 | INTERNAL-IP
152 | OS
153 | CONTAINER-RUNTIME
154 | ```
155 | 
156 | 그리고 다음을 구분한다.
157 | 
158 | ```text
159 | Node Ready
160 | → kubelet과 Control Plane의 기본 Node 상태 보고가 성립
161 | 
162 | 하지만
163 | → CNI, DNS, 특정 addon, Storage, Ingress까지 모두 정상이라는 뜻은 아님
164 | ```
165 | 
166 | ## 7. ETCD·CRI·CNI를 큰 구조로 설명하기
167 | 
168 | ### External ETCD
169 | 
170 | - Kubernetes 상태 저장소
171 | - API Server가 external ETCD endpoint를 사용
172 | - `etcdctl`로 member와 endpoint status를 확인할 수 있음
173 | - 인증서·endpoint 값은 대상 Cluster 기준으로 확인
174 | 
175 | ### CRI / containerd
176 | 
177 | - Kubernetes가 Container를 실행할 런타임
178 | - Registry 설정과 image pull 경로가 이후 workload 실행에 영향을 줌
179 | 
180 | ### CNI / Calico
181 | 
182 | - Pod Network를 구성
183 | - Pod CIDR과 실제 network plugin 설정이 연결됨
184 | - `calico-node`가 Running이라는 사실과 실제 통신 성공을 구분
185 | 
186 | 9/1에는 세부 설정을 모두 외우기보다 **ETCD=상태, CRI=Container 실행, CNI=Pod Network**라는 관계를 명확히 한다.
187 | 
188 | ## 8. 숙지 수준 분류
189 | 
190 | ### A. 문서 없이 바로 설명할 것
191 | 
192 | - [ ] Kubespray가 어떤 입력으로 Cluster를 만드는지
193 | - [ ] Ansible task 실패와 Kubernetes runtime 문제의 차이
194 | - [ ] Ansible recap에서 무엇을 보는지
195 | - [ ] API·Node·Control Plane·CNI·DNS를 왜 따로 검증하는지
196 | - [ ] `Ready` 하나로 설치 완료를 선언하면 안 되는 이유
197 | - [ ] External ETCD·containerd·Calico의 역할
198 | - [ ] VIP-A가 API 검증에서 왜 중요한지
199 | - [ ] 9/2 Storage가 별도 단계인 이유
200 | 
201 | ### B. 문서를 보며 정확히 수행·설명할 것
202 | 
203 | - [ ] `ansible-playbook` 실행 명령 찾기
204 | - [ ] Node 상태 확인 명령 찾기
205 | - [ ] `kubeadm-config`에서 전역 변수 확인 방법 찾기
206 | - [ ] Control Plane Pod 조회 방법 찾기
207 | - [ ] CoreDNS·Calico·Ingress Controller 확인 방법 찾기
208 | - [ ] ETCD member/endpoint status 확인 절차 찾기
209 | - [ ] containerd / crictl 버전·설정 확인 위치 찾기
210 | - [ ] kube-proxy mode와 node label/taint 확인 위치 찾기
211 | 
212 | ### C. 실제 실행 때 새로 확인할 것
213 | 
214 | - Playbook task 결과와 실행 시간
215 | - 실제 실패 host/task
216 | - 실제 Node 이름·Role·IP·Version
217 | - 실제 Pod 이름·IP·재시작 횟수
218 | - 실제 API health
219 | - 실제 ETCD member/leader 상태
220 | - 실제 CNI/DNS/Ingress 상태
221 | 
222 | ## 9. 내가 지금 부족한 곳을 찾는 자가점검
223 | 
224 | | 질문 | 현재 상태 | 막히는 부분 | 학습 문서 |
225 | |---|---|---|---|
226 | | `cluster.yml`이 무엇을 입력으로 사용하는지 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Kubespray]] |
227 | | Ansible recap을 보고 실패 범위를 말할 수 있는가? | 미평가 |  | 3. Kubespray |
228 | | API 정상과 Node Ready를 별도로 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
229 | | Control Plane 세 컴포넌트의 역할을 말할 수 있는가? | 미평가 |  | 3. Kubespray |
230 | | CoreDNS가 왜 별도 검증 대상인지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
231 | | Calico가 무엇을 담당하는지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
232 | | External ETCD 검증이 왜 필요한지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
233 | | containerd Registry 설정이 이후 어떤 문제와 연결되는지 설명할 수 있는가? | 미평가 |  | 3. Kubespray |
234 | | Node Ready인데 다음 날 Storage로 넘어가면 안 되는 사례를 말할 수 있는가? | 미평가 |  | [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]] |
235 | 
236 | ## 10. 읽을 문서와 목적
237 | 
238 | 1. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/03|3. Ansible Playbook 배포 및 클러스터 설정]]
239 |    - 실행과 배포 후 검증의 전체 뼈대
240 | 2. [[30. 구축 및 전환/구축 마스터 Runbook|구축 마스터 Runbook]]
241 |    - Step 3이 전체에서 차지하는 위치
242 | 3. [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
243 |    - 설치 완료를 어떤 증적으로 봐야 하는지
244 | 4. [[2026-08-31 Member 구축 1일차 - 환경 확인 및 Pre-setting]]
245 |    - Playbook 입력이 어디서 왔는지 연결
246 | 
247 | ## 11. 반드시 답할 수 있어야 할 질문
248 | 
249 | 1. `cluster.yml` 실행 전 마지막으로 무엇을 확인해야 하는가?
250 | 2. Playbook이 특정 한 노드에서만 실패했다면 무엇을 먼저 비교하는가?
251 | 3. `UNREACHABLE`과 task `FAILED`는 조사 시작점이 어떻게 다른가?
252 | 4. `kubectl get nodes`가 성공한다는 것은 무엇을 증명하는가?
253 | 5. API health와 Node Ready를 왜 모두 보는가?
254 | 6. Control Plane Pod가 모두 Running이어도 CoreDNS를 별도로 보는 이유는?
255 | 7. Calico가 비정상이면 어떤 종류의 증상이 생길 수 있는가?
256 | 8. External ETCD endpoint를 다른 Cluster 값으로 잘못 넣으면 무엇이 문제인가?
257 | 9. Ingress Controller의 NodePort와 VIP-B는 어떤 관계인가?
258 | 10. 9/2 Storage로 넘어가기 위한 최소 Kubernetes 기준은 무엇인가?
259 | 
260 | ## 12. 직접 연습할 것
261 | 
262 | ### 연습 1 — 설치 로그 판독
263 | 
264 | 과거/참조 Playbook 로그에서 다음만 먼저 찾는 연습을 한다.
265 | 
266 | ```text
267 | 첫 FAILED task
268 | 대상 host
269 | 공통 실패인가 특정 host인가
270 | recap의 failed/unreachable
271 | ```
272 | 
273 | 그 뒤에만 원인 후보를 생각한다.
274 | 
275 | ### 연습 2 — 배포 후 검증 순서 복원
276 | 
277 | 문서 없이 다음 순서를 적는다.
278 | 
279 | ```text
280 | 설계값 대조
281 | → API
282 | → Node
283 | → Control Plane
284 | → DNS
285 | → CNI
286 | → Ingress/Add-on
287 | → ETCD/Runtime 추가 확인
288 | ```
289 | 
290 | ### 연습 3 — 명령의 질문을 말하기
291 | 
292 | 아래 명령을 보기 전에 “무엇을 확인하기 위한 것인지”를 먼저 말한다.
293 | 
294 | ```bash
295 | kubectl get nodes -o wide
296 | kubectl -n kube-system describe cm kubeadm-config
297 | kubectl get pod -A -o wide
298 | kubectl get crd
299 | kubectl get svc -n ingress-nginx
300 | ```
301 | 
302 | ## 13. 정상 상태를 내가 설명할 수 있는가
303 | 
304 | ```text
305 | Playbook 실행 완료
306 | + Ansible recap에 미해결 실패 없음
307 | + API 접근 정상
308 | + 설계한 VIP/CIDR/Domain/Version 반영 확인
309 | + Node Role/Ready 상태 정상
310 | + Control Plane 핵심 Pod 정상
311 | + CoreDNS/CNI/Ingress 기본 구성 정상
312 | + ETCD/Runtime에 명백한 이상 없음
313 | =
314 | Storage 구축으로 넘어갈 Kubernetes 기반이 마련됨
315 | ```
316 | 
317 | ## 14. 문제 상황 사고 연습
318 | 
319 | ### 사례 1 — Playbook은 성공했는데 API 접속 실패
320 | 
321 | ```text
322 | 확인된 사실
323 | → Ansible task는 완료됐다.
324 | 차이
325 | → API VIP/TLS endpoint는 응답하지 않는다.
326 | 다음 판단을 가를 확인
327 | → Master 자체 API와 VIP-A 경로 중 어디가 먼저 실패하는가?
328 | ```
329 | 
330 | ### 사례 2 — 한 Node만 NotReady
331 | 
332 | ```text
333 | 전체 Cluster 재설치로 가지 않는다.
334 | → 해당 Node가 다른 Node와 무엇이 다른지 확인
335 | → kubelet / network / role / pre-setting 차이를 좁힘
336 | ```
337 | 
338 | ### 사례 3 — Node는 Ready인데 DNS가 안 됨
339 | 
340 | ```text
341 | Node Ready라는 정보의 범위를 과대해석하지 않는다.
342 | → CoreDNS Pod와 Service
343 | → Pod Network
344 | → 실제 DNS 질의
345 | 순서로 별도 기능을 확인한다.
346 | ```
347 | 
348 | ## 15. 예상 질문
349 | 
350 | | 예상 질문 | 핵심 답변 방향 | 현재 답변 가능 여부 |
351 | |---|---|---|
352 | | Playbook 성공이면 설치 성공 아닌가요? | 실행 성공과 기능 검증은 별도 | 미평가 |
353 | | 왜 `Ready` 외에 System Pod까지 보나요? | Node 상태와 Cluster 기능은 다른 증거 | 미평가 |
354 | | ETCD는 왜 Kubernetes 밖에 따로 있나요? | external ETCD 설계와 상태 저장 역할 | 미평가 |
355 | | Calico가 하는 일이 정확히 뭔가요? | Pod Network/CNI | 미평가 |
356 | | 설치가 실패하면 그냥 다시 돌리면 안 되나요? | 최초 실패 위치와 영향 범위를 먼저 고정 | 미평가 |
357 | 
358 | ## 16. 학습 기록
359 | 
360 | ### 새로 이해한 것
361 | -
362 | 
363 | ### 로그를 읽다가 막힌 것
364 | -
365 | 
366 | ### 직접 조회가 더 필요한 것
367 | -
368 | 
369 | ### 9/2로 넘길 것
370 | -
371 | 
372 | ## 17. 9/1 준비 완료 기준
373 | 
374 | - [ ] Kubespray 입력과 실행의 관계를 설명할 수 있다.
375 | - [ ] Ansible 실패를 host/task/recap으로 좁힐 수 있다.
376 | - [ ] API·Node·Control Plane·DNS·CNI를 별도 증거로 설명할 수 있다.
377 | - [ ] ETCD·CRI·CNI의 큰 역할을 설명할 수 있다.
378 | - [ ] `Node Ready ≠ DKS 전체 구축 완료`를 설명할 수 있다.
379 | - [ ] 배포 후 검증 명령을 문서에서 바로 찾을 수 있다.
380 | - [ ] 대표 실패 사례에서 다음 판단을 가를 확인 하나를 고를 수 있다.
381 | - [ ] 9/2 Storage가 시작될 수 있는 Kubernetes 기준을 말할 수 있다.
382 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증.md

Bytes: 27141
SHA-256: 7285182ec3e3a62b44c83c10c3a72a115cefe5e5f3c4262e102ca6a021735509
Lines: 1-587 of 587

```markdown
  1 | ---
  2 | title: "2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증"
  3 | status: current
  4 | doc_type: build-note
  5 | scope: "2026-09-02 신규 Member Cluster Storage Component 구성, Test PVC·Pod Mount·Write/Read 검증 및 9/3 Member 설치 선행조건 확정"
  6 | created: "2026-08-15"
  7 | updated: "2026-08-28"
  8 | parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거]]"
  9 | ---
 10 | 
 11 | # 2026-09-02 Member 구축 3일차 - Storage 구성 및 사용 검증
 12 | 
 13 | > [!important] 이 문서의 역할
 14 | > 이 문서는 9/2 신규 Member Storage 구축의 **현장 수행·판정 Source of Truth**이다. Snapshotter·Trident·Backend·StorageClass의 실제 구성과 Test PVC·Pod Mount·Write/Read·Cleanup의 정확한 수행 기준을 보존한다. 강의의 설명 순서와 Teach-back은 아래 강사용 대본을 사용하며, 상세 Manifest·명령·환경값은 이 문서와 원본 Storage Runbook을 따른다.
 15 | 
 16 | ### 9/2 강사용 대본
 17 | 
 18 | - [[출장/20. 교육/2026-09-02/오전/01. Storage 공급 경로·Snapshotter·Trident·Backend·StorageClass 강사용 전체 대본|오전 - Storage 공급 경로]]
 19 | - [[출장/20. 교육/2026-09-02/오후/01. PVC·PV·Pod Mount·Write-Read·정리·9월 3일 Gate 강사용 전체 대본|오후 - Storage 실제 사용·9/3 Gate]]
 20 | 
 21 | > [!success] 9/2 종료 Gate
 22 | > 9/3 Monitoring으로 넘어가는 판정은 `STORAGE PASS / BLOCKED`를 사용한다. `PVC Bound`만으로 통과시키지 않고 실제 Pod Mount·Write/Read·Cleanup까지 닫는다.
 23 | 
 24 | > [!success] 현재 일정의 경계
 25 | > 기존 Xi'an Host Cluster는 이미 구축 완료되어 있으며 9/2에 Host KubeSphere를 새로 설치하지 않는다. 이 문서에 남아 있는 Host installer·`cluster-configure` 설명은 **Storage가 KubeSphere와 Monitoring에 어떻게 의존되는지 이해하고, 다음날 Member 구성을 준비하기 위한 비교·배경 지식**이다. 실제 9/2 변경 범위는 신규 Member Cluster의 Storage Component 구성과 사용 검증까지다.
 26 | 
 27 | ## 1. 9/2 확정 범위
 28 | 
 29 | - External Snapshotter CRD·Controller 설치와 상태 확인
 30 | - NetApp Trident Operator·Controller·Node 구성요소 설치와 상태 확인
 31 | - Trident Backend 생성·연결 및 `online` 상태 확인
 32 | - 승인된 StorageClass 생성·기본값·reclaim policy·provisioner 확인
 33 | - Test PVC 생성과 PVC/PV 동적 Provisioning 검증
 34 | - Test Pod의 Node 배치, CSI Attach·Mount, NFS 경로와 Event 확인
 35 | - Container 내부 Mount·Write·Read·재읽기 검증
 36 | - 테스트 산출물과 임시 리소스 정리 기준 확인
 37 | - 9/3 Member Monitoring·KubeSphere가 사용할 StorageClass와 PVC 선행조건 확인
 38 | - 핵심 구간은 교육생이 직접 조회·설명·실습하고, 환경 의존 변경은 강사와 현지 담당자가 공동 확인
 39 | 
 40 | 이날 가장 중요한 문장은 다음이다.
 41 | 
 42 | > **StorageClass가 보이고 PVC가 Bound여도 Storage 교육은 끝난 것이 아니다. Pod가 실제로 Mount하고 Write/Read까지 되어야 한다.**
 43 | 
 44 | ## 2. 머릿속에 있어야 할 전체 흐름
 45 | 
 46 | ```text
 47 | 9/1 Kubernetes 기반 정상
 48 | → External Snapshotter CRD·Controller
 49 | → Trident Operator / Controller / Node CSI
 50 | → Trident Backend 연결 및 online 확인
 51 | → 승인된 StorageClass 생성·속성 확인
 52 | → PVC 동적 Provisioning
 53 | → PV·VolumeHandle·NFS export 경로 확인
 54 | → Test Pod Scheduling
 55 | → Node에서 실제 NFS Mount
 56 | → Container Write / Read / 재읽기
 57 | → 테스트 리소스와 증적 정리
 58 | → 9/3 Member Monitoring PVC 선행조건 확인
 59 | → Member KubeSphere 설치·기존 Host Join 준비
 60 | ```
 61 | 
 62 | ### 서로 다른 성공 단계
 63 | 
 64 | ```text
 65 | StorageClass 존재
 66 | ≠ Backend 정상
 67 | 
 68 | PVC Bound
 69 | ≠ Pod Mount
 70 | 
 71 | Pod Ready
 72 | ≠ Volume 실제 Write/Read 확인
 73 | 
 74 | Test PVC·Mount·Write/Read 성공
 75 | ≠ 9/3 Member Monitoring·KubeSphere·Host Join 완료
 76 | ```
 77 | 
 78 | ## 3. Storage 구성요소 관계를 설명하기
 79 | 
 80 | 근거: [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Kubernetes 스토리지 컴포넌트 구축 및 설치 검증]]
 81 | 
 82 | ### External Snapshotter
 83 | 
 84 | - CSI Snapshot API/Controller 선행 구성
 85 | - Snapshot CRD와 Controller가 준비됨
 86 | - Trident와 동일한 것은 아님
 87 | 
 88 | ### NetApp Trident
 89 | 
 90 | - Kubernetes CSI와 NetApp Storage를 연결
 91 | - Operator / Controller / Node 구성요소
 92 | - Backend를 통해 SVM·Data LIF·Storage 정책과 연결
 93 | 
 94 | ### Backend
 95 | 
 96 | - Kubernetes 바깥의 실제 NetApp Storage 정보를 Trident와 연결
 97 | - `online` 여부가 중요
 98 | - management LIF·Data LIF·SVM·export policy 등은 실제 환경값 확인 필요
 99 | 
100 | ### StorageClass
101 | 
102 | - 사용자가 PVC에서 선택할 Storage 공급 정책
103 | - Xi'an의 현재 기준은 `scs-netapp-qtree-nfs-sc-delete`
104 | - provisioner는 Trident CSI와 연결
105 | 
106 | ### PVC / PV / Pod
107 | 
108 | ```text
109 | PVC
110 | → StorageClass 요청
111 | → Trident가 volume provision
112 | → PV 연결
113 | → kubelet/CSI가 Node에 Mount
114 | → Container가 filesystem 사용
115 | ```
116 | 
117 | 이 연결을 그림 없이 설명할 수 있어야 한다.
118 | 
119 | ## 4. `Bound`와 `Mount`를 분리해서 이해하기
120 | 
121 | 9/2와 9/3 모두에서 반복해서 사용할 핵심이다.
122 | 
123 | ```text
124 | PVC Bound
125 | → Kubernetes/CSI가 volume을 할당하는 단계까지 성공
126 | 
127 | Pod Mount 성공
128 | → 해당 Node에서 실제 NFS export를 붙이는 단계까지 성공
129 | 
130 | Write/Read 성공
131 | → Container에서 실제 filesystem을 사용할 수 있음
132 | ```
133 | 
134 | 따라서 `Bound` 후 `ContainerCreating + FailedMount`는 모순이 아니다.
135 | 
136 | 관련 사례:
137 | [[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우]]
138 | 
139 | ## 5. Kubernetes와 ONTAP의 책임 경계를 이해하기
140 | 
141 | Storage 문제를 모두 Kubernetes 문제로 보거나 모두 Storage 문제로 넘기지 않는다.
142 | 
143 | ### Kubernetes/Trident 측에서 볼 수 있는 것
144 | 
145 | - StorageClass
146 | - PVC/PV
147 | - CSI driver
148 | - Trident backend state
149 | - Pod Event
150 | - kubelet Mount 오류
151 | - Node가 선택한 NFS source path
152 | 
153 | ### Storage/Network 측과 연결되는 것
154 | 
155 | - Data LIF
156 | - Node Source IP
157 | - Route
158 | - TCP 2049
159 | - Export policy
160 | - 실제 NFS export path
161 | 
162 | 문제가 생기면 “Trident 문제”라고 바로 부르지 않고 **Provisioning이 실패한 것인지 Mount가 실패한 것인지 먼저 구분**한다.
163 | 
164 | ## 6. 9/3 Member 구성과 연결되는 Storage 의존성
165 | 
166 | 근거:
167 | - [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
168 | - [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
169 | 
170 | 9/2의 Storage 검증은 독립된 기능 점검으로 끝나지 않는다. 다음날 구성할 Member Monitoring과 KubeSphere가 PVC를 실제로 사용할 수 있어야 하므로, **테스트 PVC 한 건의 성공을 다음 구성요소의 선행조건으로 해석하는 연결**이 필요하다.
171 | 
172 | ```text
173 | StorageClass 사용 가능
174 | → Monitoring PVC 동적 Provisioning 가능
175 | → Prometheus·Grafana Pod가 Volume Mount 가능
176 | → Member Monitoring 데이터 보존 가능
177 | → Member KubeSphere 설치의 Storage 의존성 충족
178 | → 기존 Host Join 전 Member 자체 상태 검증 가능
179 | ```
180 | 
181 | ### 9/3 전에 확정할 Storage 항목
182 | 
183 | - Member Monitoring이 사용할 StorageClass 이름
184 | - StorageClass의 provisioner, reclaim policy, volumeBindingMode
185 | - Trident Backend `online` 상태와 실제 SVM·Data LIF 연결
186 | - Router·Infra·Worker를 포함한 대상 Node에서 NFS Data LIF 접근 가능 여부
187 | - Test PVC가 생성한 PV의 VolumeHandle과 실제 export path
188 | - Pod가 스케줄된 Node와 Mount source의 일치 여부
189 | - Container에서 Write한 데이터가 재읽기되는지
190 | - 테스트 리소스 삭제 시 PV와 Backend Volume의 정리 동작
191 | - 9/3에 사용할 PVC 용량과 Namespace
192 | - 실패 시 9/3 작업을 시작하지 않을 중단 기준
193 | 
194 | ### 기존 Host KubeSphere 문서를 남겨 두는 이유
195 | 
196 | 기존 Xi'an Host Cluster는 이미 구축 완료되어 있고 이번 출장에서는 재설치하지 않는다. 다만 Host의 KubeSphere·Monitoring도 StorageClass, Registry, External ETCD, Node 배치 정책에 의존하므로 다음 두 파일의 역할을 **비교 지식**으로 이해할 필요가 있다.
197 | 
198 | #### `kubesphere-installer.yaml`
199 | 
200 | - KubeSphere installer 실행을 위한 CRD·RBAC·Deployment 생성
201 | - installer Pod의 Image와 Registry 의존성
202 | - Infra Node 배치 정책
203 | - 설치 실행기 자체의 기동 조건
204 | 
205 | #### `cluster-configure.yaml`
206 | 
207 | - KubeSphere 기능과 환경 설정
208 | - StorageClass와 Monitoring Storage
209 | - Registry와 External ETCD
210 | - Console·Ingress
211 | - Multi-Cluster Role
212 | - 기능 Module별 구성
213 | 
214 | > `kubesphere-installer.yaml`은 설치 실행기를 올리고, `cluster-configure.yaml`은 그 실행기가 어떤 KubeSphere 구성을 만들지 정의한다. 이번 9/2에는 이 두 파일을 Host에 적용하지 않고, **Storage가 다음날 Member 설치와 Monitoring에 어떻게 연결되는지 설명하는 비교 근거**로만 사용한다.
215 | 
216 | ## 7. Storage 검증 증적을 단계별로 남기는 법
217 | 
218 | 한 장의 `kubectl get pvc` 출력으로 완료를 선언하지 않는다. 각 단계에서 서로 다른 질문에 답하는 증적을 남긴다.
219 | 
220 | | 단계 | 핵심 질문 | 최소 증적 | 실패 시 첫 분기 |
221 | |---|---|---|---|
222 | | Snapshotter | Snapshot API·Controller가 준비됐는가? | CRD와 Controller 상태 | CRD 누락 / Controller 비정상 |
223 | | Trident | CSI Controller·Node가 준비됐는가? | Trident Pod·DaemonSet 상태 | 특정 Node 누락 / Image·권한 오류 |
224 | | Backend | NetApp 연결이 성립했는가? | `tridentctl get backend`의 `online` | SVM·LIF·Credential·Network |
225 | | StorageClass | 승인된 정책이 노출됐는가? | YAML의 provisioner·parameter·reclaim policy | 오타 / 잘못된 Backend·정책 |
226 | | Provisioning | PVC 요청이 PV로 연결됐는가? | PVC·PV·Event·VolumeHandle | Pending / Provisioner Event |
227 | | Mount | 선택된 Node가 NFS export를 붙였는가? | Pod Event·Mount source·Node | Route·2049·Export policy |
228 | | 사용 | Container가 실제 파일시스템을 쓰는가? | `df`, write, read, 재읽기 | 권한·filesystem·mount option |
229 | | 정리 | 테스트 자원이 기대대로 정리되는가? | PVC/PV/Backend Volume 상태 | reclaim policy·잔여 Volume |
230 | 
231 | ### 증적 기록 양식
232 | 
233 | ```text
234 | Cluster/context: ______________________________
235 | Namespace: ___________________________________
236 | StorageClass: _________________________________
237 | Backend/state: ________________________________
238 | PVC/PV: ______________________________________
239 | Pod/Node: ____________________________________
240 | NFS source/export path: _______________________
241 | Write test: __________________________________
242 | Read-back test: _______________________________
243 | Cleanup result: ______________________________
244 | 첫 실패 단계 또는 미확인 단계: ________________
245 | 다음 읽기 전용 확인: __________________________
246 | ```
247 | 
248 | 실제 IP, SVM, Credential, Secret 원문은 교육 문서에 복사하지 않는다. 필요한 경우 화면을 마스킹하고, 값 자체보다 **어느 단계가 어떤 근거로 통과했는지**를 남긴다.
249 | 
250 | ## 8. 9/3 진행 여부를 가르는 Gate
251 | 
252 | 다음 항목이 모두 충족되어야 Member Monitoring·KubeSphere 단계로 이동한다.
253 | 
254 | 1. Kubernetes API·Node·CNI·DNS 기본 검증이 9/1 기준으로 통과했다.
255 | 2. Snapshotter와 Trident의 필수 구성요소가 대상 Node 전체에서 정상이다.
256 | 3. Backend가 `online`이며 승인된 SVM·Data LIF를 참조한다.
257 | 4. StorageClass가 승인된 값과 일치하고 잘못된 예시값을 사용하지 않는다.
258 | 5. Test PVC가 Bound되고 대응 PV·VolumeHandle을 확인했다.
259 | 6. Test Pod가 실제 Node에 배치되어 NFS Volume을 Mount했다.
260 | 7. Container에서 Write와 Read-back을 성공했다.
261 | 8. 테스트 리소스 정리 동작과 잔여 Volume 여부를 확인했다.
262 | 9. Monitoring에서 사용할 StorageClass·Namespace·용량을 확정했다.
263 | 10. 9/3 Monitoring의 실제 Storage 사용을 막는 미해결 Storage 오류가 없다. 비차단 기록 항목이 남으면 영향·담당자·기한을 별도로 기록하되 `STORAGE PASS` 자체를 흐리지 않는다.
264 | 
265 | ### 중단 기준
266 | 
267 | - Backend가 `offline`이거나 실제 연결 대상이 미확정
268 | - StorageClass가 과거 Cluster의 값인지 현재 신규 Member 값인지 구분되지 않음
269 | - PVC가 Pending 상태로 원인이 해소되지 않음
270 | - PVC는 Bound지만 Pod가 `FailedMount`에서 멈춤
271 | - Mount는 됐지만 Write/Read 검증 실패
272 | - Node별 NFS 접근 조건이 서로 달라 특정 역할 Node에서만 실패
273 | - 테스트 정리 과정에서 의도하지 않은 PV·Backend Volume 삭제 위험이 확인됨
274 | 
275 | 이 경우 9/3 KubeSphere 설치를 강행하지 않는다. 먼저 실패 단계를 확정하고, Kubernetes·Network·ONTAP 중 어느 담당 영역의 확인이 필요한지 분리한다.
276 | 
277 | ### 다음날 installer 로그와 연결되는 판단
278 | 
279 | 9/3에는 다음 두 실패를 구분해야 한다.
280 | 
281 | ```text
282 | Monitoring PVC 자체가 Pending 또는 FailedMount인가?
283 | vs
284 | Storage는 정상인데 installer 내부 monitoring task가 실패하는가?
285 | ```
286 | 
287 | 첫 번째는 9/2 Storage Gate의 미통과 가능성이 높고, 두 번째는 CRD·설치 순서·설정값·Image·권한 같은 KubeSphere 설치 영역을 확인해야 한다. Pod가 `Running`이라는 한 상태만으로 어느 쪽도 성공이라고 판정하지 않는다.
288 | 
289 | ## 9. 숙지 수준 분류
290 | 
291 | ### A. 문서 없이 바로 설명할 것
292 | 
293 | - [ ] Snapshotter·Trident·Backend·StorageClass·PVC·PV의 관계
294 | - [ ] `PVC Bound ≠ Pod Mount ≠ Write/Read`인 이유
295 | - [ ] Provisioning 실패와 Node Mount 실패의 조사 시작점 차이
296 | - [ ] NFS Mount에서 Kubernetes·Network·ONTAP의 책임 경계
297 | - [ ] Backend `online`이 의미하는 범위와 의미하지 않는 범위
298 | - [ ] StorageClass의 provisioner·reclaim policy·volumeBindingMode가 영향을 주는 지점
299 | - [ ] 9/2 Storage 검증이 9/3 Monitoring·KubeSphere의 선행조건인 이유
300 | - [ ] 기존 Host를 재설치하지 않지만 Host 문서를 비교 지식으로 남기는 이유
301 | - [ ] Monitoring PVC 문제와 installer task 문제를 구분하는 기준
302 | - [ ] 테스트 리소스 정리 결과까지 확인해야 하는 이유
303 | 
304 | ### B. 문서를 보며 수행·설명할 것
305 | 
306 | - [ ] Snapshot CRD·Controller 확인
307 | - [ ] Trident Operator·Controller·Node Pod 확인
308 | - [ ] `tridentctl` Backend 조회와 상태 해석
309 | - [ ] StorageClass YAML의 핵심값 확인
310 | - [ ] Test PVC·PV·Event·VolumeHandle 확인
311 | - [ ] Test Pod의 Node·Event·Mount source 확인
312 | - [ ] Container 내부 `df`·mount·Write·Read·재읽기 확인
313 | - [ ] Node에서 Data LIF Route와 TCP 2049 확인 위치 찾기
314 | - [ ] Export policy 확인 요청에 필요한 Source IP와 export path 정리
315 | - [ ] 테스트 PVC 삭제 후 PV·Backend Volume 정리 상태 확인
316 | - [ ] 9/3 Member Monitoring PVC의 StorageClass·용량·Namespace 확인
317 | - [ ] 기존 Host installer·cluster-configure에서 Storage 의존값을 비교해 찾기
318 | 
319 | ### C. 실제 환경에서 확인할 것
320 | 
321 | - 실제 Backend name·state·SVM·Data LIF
322 | - 실제 StorageClass 이름과 승인 근거
323 | - 실제 PV·VolumeHandle·NFS export path
324 | - 실제 Test Pod 이름·Node·Mount source
325 | - 역할별 Node의 Data LIF 접근 차이
326 | - 실제 Write 내용과 Read-back 결과
327 | - 테스트 리소스 정리 결과와 잔여 Volume
328 | - 9/3 Monitoring용 StorageClass·PVC 용량·Namespace
329 | - Storage 미해결 항목의 담당자·영향·다음 조치
330 | - Secret·Credential 원문을 노출하지 않은 증적 기록 방식
331 | 
332 | ## 10. 내가 지금 부족한 곳을 찾는 자가점검
333 | 
334 | | 질문 | 현재 상태 | 막히는 부분 | 학습 문서 |
335 | |---|---|---|---|
336 | | Snapshotter와 Trident의 차이를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Storage]] |
337 | | Trident Backend가 무엇이며 `online`은 어디까지 증명하는가? | 미평가 |  | 4. Storage |
338 | | PVC→PV→CSI→Node Mount→Write/Read 흐름을 그릴 수 있는가? | 미평가 |  | 4. Storage |
339 | | `Bound`인데 Mount가 실패할 수 있는 이유를 설명할 수 있는가? | 미평가 |  | Storage 트러블슈팅 |
340 | | Node→Data LIF 경로와 Export policy가 왜 함께 중요한지 설명할 수 있는가? | 미평가 |  | Storage 트러블슈팅 |
341 | | StorageClass의 provisioner·reclaim policy·volumeBindingMode를 읽을 수 있는가? | 미평가 |  | 4. Storage |
342 | | Test Pod의 Event에서 Provisioning과 Mount 실패를 구분할 수 있는가? | 미평가 |  | 4. Storage |
343 | | Write/Read 검증과 테스트 리소스 정리 결과를 기록할 수 있는가? | 미평가 |  | 4. Storage |
344 | | 9/3 Monitoring PVC가 사용할 StorageClass·용량·Namespace를 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2 Member]] |
345 | | Monitoring PVC 실패와 installer task 실패를 구분할 기준이 있는가? | 미평가 |  | 5-2 Member |
346 | | 기존 Host 문서가 이번 9/2 실제 수행 범위가 아니라 비교 근거라는 점을 설명할 수 있는가? | 미평가 |  | [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-1|5-1 Host]] |
347 | 
348 | ## 11. 읽을 문서와 목적
349 | 
350 | 1. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/04|4. Kubernetes 스토리지 컴포넌트 구축 및 설치 검증]]
351 |    - Snapshotter→Trident→Backend→StorageClass→PVC→Mount→Write/Read의 전체 선후관계와 실제 명령·검증 기준
352 | 2. [[50. 운영/08. 트러블슈팅/Kubernetes/03. NetApp NFS PVC는 Bound인데 Pod Mount가 실패하는 경우|NFS PVC Mount 실패]]
353 |    - Provisioning 성공과 Node Mount 실패를 분리하고, Data LIF·Source IP·Route·TCP 2049·Export policy로 확장하는 실제 사례
354 | 3. [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
355 |    - StorageClass 존재가 아니라 Test PVC·Pod Mount·Write/Read까지 완료 증적으로 보는 기준
356 | 4. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5-2. KubeSphere Member 클러스터 설치]]
357 |    - 9/3 Monitoring PVC·Member KubeSphere·기존 Host Join에 필요한 Storage 의존성
358 | 5. [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
359 |    - Member Monitoring 선행 구성과 KubeSphere 설치 순서
360 | 6. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-1|5-1. KubeSphere Host 클러스터 설치 및 운영 구성]]
361 |    - 기존 Host가 이미 구축되어 있다는 전제에서 installer·cluster-configure·Storage 의존성을 비교하는 참고
362 | 7. [[30. 구축 및 전환/Host 클러스터/05.1.1 Apply kubesphere-installer|KubeSphere Installer 적용]]
363 |    - 실행기와 배치·Registry 의존성을 비교할 때만 사용하며 이번 9/2 적용 대상은 아님
364 | 8. [[30. 구축 및 전환/Host 클러스터/05.1.2 Apply cluster-configure|Host cluster-configure 적용]]
365 |    - KubeSphere가 StorageClass·Monitoring Storage를 소비하는 구조를 확인하는 비교 자료
366 | 
367 | ## 12. 반드시 답할 수 있어야 할 질문
368 | 
369 | 1. 왜 External Snapshotter CRD·Controller를 Trident와 분리해 확인하는가?
370 | 2. Trident Backend와 StorageClass는 어떤 관계이고, `online`은 어디까지 증명하는가?
371 | 3. PVC가 Bound라는 것은 정확히 어느 단계까지 성공했다는 뜻인가?
372 | 4. Pod Mount는 어떤 Event·Node·NFS source 증적으로 확인하는가?
373 | 5. Container Write·Read·재읽기 검증은 왜 별도로 필요한가?
374 | 6. NFS Mount 실패 시 Node Route·TCP 2049·Export policy·Source IP는 어떻게 연결되는가?
375 | 7. StorageClass의 provisioner·reclaim policy·volumeBindingMode는 각각 어떤 동작에 영향을 주는가?
376 | 8. 테스트 PVC 삭제 후 PV와 Backend Volume 정리를 왜 확인해야 하는가?
377 | 9. 9/3 Monitoring PVC가 Storage Gate를 통과했다고 판단하려면 무엇이 필요한가?
378 | 10. Monitoring PVC가 Pending인 상황과 installer 내부 monitoring task가 실패한 상황은 어떻게 구분하는가?
379 | 11. 기존 Host installer 문서가 이번 9/2 실제 적용 대상이 아닌데도 참고하는 이유는 무엇인가?
380 | 12. 어떤 Storage 실패가 남아 있으면 9/3 Member KubeSphere 작업을 중단해야 하는가?
381 | 
382 | ## 13. 직접 연습할 것
383 | 
384 | ### 연습 1 — Storage 전체 흐름 5분 설명
385 | 
386 | ```text
387 | Snapshotter
388 | → Trident
389 | → Backend
390 | → StorageClass
391 | → PVC
392 | → PV
393 | → Pod Mount
394 | → Write/Read
395 | ```
396 | 
397 | 각 화살표에서 “무엇이 다음 단계의 조건인가?”를 말한다.
398 | 
399 | ### 연습 2 — 정상 출력과 실패 출력 구분
400 | 
401 | 다음 세 장면을 비교해서 현재 실패 위치를 말한다.
402 | 
403 | ```text
404 | A. PVC Pending
405 | B. PVC Bound + Pod ContainerCreating + FailedMount
406 | C. PVC Bound + Pod Running + df/write/read 성공
407 | ```
408 | 
409 | ### 연습 3 — Storage 증적표 완성
410 | 
411 | 정상 또는 실패 출력 한 세트를 사용해 다음 표를 실제 값으로 채운다. Secret·Credential 원문은 쓰지 않는다.
412 | 
413 | ```text
414 | Backend / state:
415 | StorageClass / provisioner / reclaim policy:
416 | PVC / phase / Event:
417 | PV / VolumeHandle:
418 | Pod / Node:
419 | NFS source / export path:
420 | Mount 확인:
421 | Write / Read-back:
422 | Cleanup 결과:
423 | 첫 실패 단계:
424 | 다음 읽기 전용 확인:
425 | ```
426 | 
427 | 출력에 없는 값은 추측하지 않고 `미확인`으로 둔다. 한 단계의 성공으로 뒤 단계를 자동 통과시키지 않는다.
428 | 
429 | ### 연습 4 — 9/3 Member 선행조건 점검
430 | 
431 | `05-2.md`와 Member 클러스터 개요에서 다음 항목을 찾고, 각각 9/2 Storage 결과와 어떻게 연결되는지 한 문장씩 설명한다.
432 | 
433 | ```text
434 | Monitoring StorageClass
435 | Prometheus PVC
436 | Grafana PVC 또는 datasource 의존성
437 | Infra nodeSelector / taint·toleration
438 | Member clusterRole
439 | Registry
440 | External ETCD Monitoring 대상
441 | 기존 Host Join 전 Member 정상 조건
442 | ```
443 | 
444 | ### 연습 5 — 기존 Host 문서를 비교 근거로 읽기
445 | 
446 | `05-1.md`에서 다음 값을 찾되, **9/2에 Host에 적용하지 않는다.** 같은 항목이 Member 구성에서는 어떤 값과 역할로 나타나는지 비교한다.
447 | 
448 | ```text
449 | StorageClass
450 | local_registry
451 | External ETCD
452 | multicluster.clusterRole
453 | infra nodeSelector
454 | ```
455 | 
456 | ### 연습 6 — 실행기와 구성의 역할 설명
457 | 
458 | 문서를 닫고 90초 안에 다음 관계를 설명한다. 목적은 Host 설치 실행이 아니라 다음날 Member installer 로그를 읽을 준비다.
459 | 
460 | ```text
461 | kubesphere-installer.yaml
462 | vs
463 | cluster-configure.yaml
464 | vs
465 | Monitoring PVC의 Storage 선행조건
466 | ```
467 | 
468 | ## 14. 정상 상태를 내가 설명할 수 있는가
469 | 
470 | ### Storage
471 | 
472 | ```text
473 | Trident 구성요소 정상
474 | → backend online
475 | → StorageClass 정상
476 | → PVC Bound
477 | → PV/CSI 연결 확인
478 | → Pod Ready
479 | → 실제 Mount
480 | → Write/Read
481 | ```
482 | 
483 | ### 9/3 Member 구성 진입 준비
484 | 
485 | ```text
486 | Storage Gate 통과
487 | → Monitoring에서 사용할 StorageClass·PVC 조건 확정
488 | → Member installer·cluster-configure의 Storage/Registry/ETCD/Role 값 사전 대조
489 | → 기존 Host는 재설치하지 않고 접근·Join 대상만 확인
490 | → 9/3 Member Monitoring·KubeSphere 설치와 Host Join을 시작할 수 있음
491 | ```
492 | 
493 | ### 완료를 선언하지 않는 상태
494 | 
495 | ```text
496 | PVC Bound만 확인
497 | 또는
498 | 한 Node에서만 Mount 성공
499 | 또는
500 | Write/Read 없이 Pod Running만 확인
501 | 또는
502 | 테스트 정리 결과 미확인
503 | =
504 | Storage 완료 아님, 9/3 진행 Gate 미통과
505 | ```
506 | 
507 | ## 15. 문제 상황 사고 연습
508 | 
509 | ### 사례 1 — PVC Bound, Pod Mount 실패
510 | 
511 | ```text
512 | 확인된 사실
513 | → Provisioning은 통과했다.
514 | 차이
515 | → Pod가 Node에서 NFS를 Mount하지 못한다.
516 | 다음 분기
517 | → Pod Event의 NFS path와 해당 Node의 Data LIF route/TCP 2049를 본다.
518 | ```
519 | 
520 | ### 사례 2 — Backend offline
521 | 
522 | ```text
523 | Pod 문제로 바로 가지 않는다.
524 | → Backend 자체 연결이 성립하지 않았으므로 Storage 연결 정보를 먼저 확인한다.
525 | ```
526 | 
527 | ### 사례 3 — Test Storage는 정상인데 9/3 Monitoring PVC가 Pending
528 | 
529 | ```text
530 | 9/2 Test PVC 성공을 자동으로 모든 Monitoring PVC 성공으로 확대하지 않는다.
531 | → Monitoring PVC가 같은 StorageClass를 사용하는가?
532 | → 요청 용량과 Namespace Quota가 맞는가?
533 | → volumeBindingMode와 실제 Pod Scheduling 조건은 무엇인가?
534 | → 해당 Infra Node에서 Data LIF 접근이 되는가?
535 | → PVC Event의 최초 실패 원문은 무엇인가?
536 | ```
537 | 
538 | Test PVC와 Monitoring PVC는 같은 Storage 기반을 사용하더라도 요청 용량·Namespace·Node 배치·Quota가 다를 수 있다. 9/3에는 Storage 자체 실패와 KubeSphere installer 내부 task 실패를 먼저 분리한다.
539 | 
540 | ## 16. 예상 질문
541 | 
542 | | 예상 질문 | 핵심 답변 방향 | 현재 답변 가능 여부 |
543 | |---|---|---|
544 | | PVC가 Bound면 왜 Pod가 못 뜰 수 있나요? | Provisioning과 Node Mount 단계 분리 | 미평가 |
545 | | Trident는 StorageClass인가요? | CSI/Backend와 정책 객체의 역할 구분 | 미평가 |
546 | | Backend가 online이면 Storage는 끝난 건가요? | Backend 연결과 PVC·Node Mount·Write/Read는 별도 | 미평가 |
547 | | Test PVC가 성공하면 Monitoring PVC도 무조건 되나요? | Namespace·Quota·용량·Node 배치 조건을 별도 검증 | 미평가 |
548 | | 왜 테스트 리소스 삭제 결과까지 보나요? | reclaim policy와 잔여 Volume 동작도 운영 기준 | 미평가 |
549 | | 9/3 installer의 monitoring task가 실패하면 Storage를 다시 설치해야 하나요? | Monitoring PVC 상태와 CRD·Endpoint·installer task를 먼저 분리 | 미평가 |
550 | | 기존 Host KubeSphere 문서는 왜 읽나요? | 이번 적용 대상이 아니라 Storage 의존성을 비교하는 배경 근거 | 미평가 |
551 | 
552 | ## 17. 학습 기록
553 | 
554 | ### 새로 이해한 것
555 | -
556 | 
557 | ### 설명하다 막힌 것
558 | -
559 | 
560 | ### 직접 해봐야 할 것
561 | -
562 | 
563 | ### 9/3에 이어서 볼 Member Monitoring·KubeSphere 영역
564 | -
565 | 
566 | ### Storage Gate에서 아직 미확정인 실제값
567 | -
568 | 
569 | ### 9/3 시작 전에 담당자 확인이 필요한 항목
570 | -
571 | 
572 | ## 18. 9/2 준비 완료 기준
573 | 
574 | - [ ] Storage 전체 흐름을 문서 없이 설명할 수 있다.
575 | - [ ] `PVC Bound ≠ Mount ≠ Write/Read`를 명확히 설명할 수 있다.
576 | - [ ] Kubernetes·Network·ONTAP의 책임 경계를 나눌 수 있다.
577 | - [ ] Snapshotter·Trident Backend·StorageClass·PVC·PV의 관계를 설명할 수 있다.
578 | - [ ] Backend `online`이 PVC·Mount·Write/Read 전체 성공을 뜻하지 않는다고 설명할 수 있다.
579 | - [ ] StorageClass의 provisioner·reclaim policy·volumeBindingMode를 읽을 수 있다.
580 | - [ ] Test PVC의 PV·VolumeHandle·Pod Node·NFS source를 증적으로 연결할 수 있다.
581 | - [ ] Container Write·Read·재읽기와 테스트 리소스 정리 결과를 확인할 수 있다.
582 | - [ ] 대표 Storage 실패에서 다음 판단을 가를 읽기 전용 확인 하나를 고를 수 있다.
583 | - [ ] 9/3 Member Monitoring이 사용할 StorageClass·Namespace·용량을 확정할 수 있다.
584 | - [ ] Monitoring PVC 실패와 KubeSphere installer 내부 monitoring task 실패를 구분할 수 있다.
585 | - [ ] 기존 Host installer 문서는 비교 근거이며 9/2 실제 적용 대상이 아님을 설명할 수 있다.
586 | - [ ] 9/3 Member Monitoring·KubeSphere·기존 Host Join으로 넘어갈 Storage Gate를 판정할 수 있다.
587 | 
```

### 01. 활성 프로젝트/01. Xi'an 전환 운영 가이드/출장/30. 구축/2026-09-03 Member 구축 4일차 - Monitoring KubeSphere Host Join 및 최종 인수.md

Bytes: 42449
SHA-256: dd6de41e621dfdc32a03bd2f3e5c42fb6f15eb6531ab9a1a3ef73d7a20d2c672
Lines: 1-1489 of 1489

```markdown
   1 | ---
   2 | title: "2026-09-03 Member 구축 4일차 - Monitoring·KubeSphere·기존 Host Join 및 최종 인수"
   3 | status: current
   4 | doc_type: build-note
   5 | scope: "2026-09-03 신규 Member Monitoring 구성, Member KubeSphere 설치·검증, 기존 Host Join, Multi-Cluster 확인 및 전체 구축 최종 인수"
   6 | created: "2026-08-15"
   7 | updated: "2026-08-28"
   8 | parent: "[[2026-08-24~09-04 Xi'an 현지 교육 실행 일정 및 근거|Xi'an DKS Member Cluster 구축 및 운영 기술 전수 계획]]"
   9 | ---
  10 | 
  11 | # 2026-09-03 Member 구축 4일차 - Monitoring·KubeSphere·기존 Host Join 및 최종 인수
  12 | 
  13 | > [!important] 이 문서의 역할
  14 | > 이 문서는 9/3 신규 Member Monitoring·KubeSphere·Host Join·최종 인수의 **현장 수행·판정 Source of Truth**이다. 정확한 Manifest·Join 절차·증적 기준과 환경 의존값을 보존한다. 강의의 설명 순서와 Teach-back은 아래 네 개의 강사용 대본으로 분리해 사용하며, 실제 변경은 이 문서와 해당 원본 Runbook을 따른다.
  15 | 
  16 | ### 9/3 강사용 대본
  17 | 
  18 | - [[출장/20. 교육/2026-09-03/오전/01. Member Monitoring 전체 경로·Target·Grafana 강사용 전체 대본|오전 1 - Member Monitoring]]
  19 | - [[출장/20. 교육/2026-09-03/오전/02. Member KubeSphere 설치·기능·Pre-Join Gate 강사용 전체 대본|오전 2 - Member KubeSphere·Pre-Join Gate]]
  20 | - [[출장/20. 교육/2026-09-03/오후/01. 기존 Host Join·Multi-Cluster 기능 검증 강사용 전체 대본|오후 1 - 기존 Host Join·Multi-Cluster 검증]]
  21 | - [[출장/20. 교육/2026-09-03/오후/02. 전체 구축 최종 인수·증적·잔여 항목 강사용 전체 대본|오후 2 - 최종 인수]]
  22 | 
  23 | > [!success] 9/3 Gate 체계
  24 | > 오전에는 `MONITORING PASS / BLOCKED`, `MEMBER SELF PASS / BLOCKED`, 오후 Join은 `MULTI-CLUSTER PASS / BLOCKED`를 사용한다. `PASS / PARTIAL / BLOCKED`는 모든 핵심 기능 검증이 끝난 **최종 인수에서만** 사용한다.
  25 | 
  26 | > [!success] Host 전제
  27 | > 기존 Xi'an Host Cluster는 이미 구축 완료되어 있다. 9/3에는 Host KubeSphere를 새로 설치하거나 재구성하지 않는다. 기존 Host는 **접근·상태·Join 대상·Multi-Cluster 관리면**만 확인한다. 이번 출장의 신규 구축 대상은 Member Cluster이며, 최종 완료 조건은 신규 Member 자체 정상과 기존 Host Join 후 Multi-Cluster 정상 상태다.
  28 | 
  29 | > [!warning] 보호된 값
  30 | > ETCD Certificate Secret, kubeconfig, JWT, Host Join용 Secret, Token, Private Key, Password는 화면·문서·로그에 원문을 남기지 않는다. 존재·이름·Type·Key 구조·전달 경로만 승인된 방식으로 확인한다.
  31 | 
  32 | ## 1. 9/3 확정 범위
  33 | 
  34 | ### 오전 — Member Monitoring과 Member KubeSphere
  35 | 
  36 | - 9/2 Storage Gate 재확인
  37 | - 대상 Member context·Node·StorageClass·Registry·Domain·ETCD 실제값 확인
  38 | - `monitoring` Namespace와 Preliminary Components 확인
  39 | - ETCD Certificate Secret 확인
  40 | - Grafana·Prometheus·Alertmanager PVC 선행조건 확인
  41 | - Prometheus Operator CRD 적용·`Established` 검증
  42 | - DKS custom `kube-prometheus-stack` 적용
  43 | - Prometheus·Alertmanager·Grafana Pod·PVC·배치 검증
  44 | - Monitoring Ingress 적용·VIP-B 경로 확인
  45 | - External ETCD Service·Endpoints·ServiceMonitor 구성
  46 | - Prometheus ETCD Target `UP` 확인
  47 | - Grafana datasource·Dashboard 확인
  48 | - Member KubeSphere installer·ClusterConfiguration 적용
  49 | - Member 외부 Monitoring Endpoint·Storage·Registry·ETCD·Role 검증
  50 | - KubeSphere Platform Workload 배치와 installer 완료 확인
  51 | 
  52 | ### 오후 — 기존 Host Join과 최종 인수
  53 | 
  54 | - 신규 Member 자체 최종 Pre-Join 검증
  55 | - 기존 Host 접근·상태·Join 대상 확인
  56 | - 승인된 방식으로 Host Join 수행
  57 | - Member Agent·연결 Component 상태 확인
  58 | - Host Console에서 신규 Member 등록·상태 확인
  59 | - Host에서 Member Resource·Monitoring 관리·관측 확인
  60 | - Multi-Cluster 경로·권한·통신 확인
  61 | - 8/31~9/3 전체 구축 증적 통합
  62 | - 미완료·Blocker·현장 확인사항·Q&A 정리
  63 | - 9/4 철수 전 인계할 문서·증적·접근 상태 확정
  64 | 
  65 | 이날의 핵심 질문은 다음이다.
  66 | 
  67 | > **신규 Member의 Monitoring·KubeSphere·기존 Host Join은 각각 무엇을 완성하며, 어떤 증거가 있어야 신규 Member가 Xi'an Multi-Cluster의 운영 가능한 구성원으로 최종 인수됐다고 말할 수 있는가?**
  68 | 
  69 | ## 2. 전체 선후관계
  70 | 
  71 | ```text
  72 | 9/2 Storage Gate 통과
  73 | → 대상 Member context·identity·actual values 재확인
  74 | → monitoring Namespace
  75 | → ETCD Certificate Secret
  76 | → Grafana / Prometheus / Alertmanager Storage 선행조건
  77 | → Prometheus Operator CRD
  78 | → DKS custom kube-prometheus-stack
  79 | → Monitoring Pod·PVC·Node 배치
  80 | → Monitoring Ingress·VIP-B
  81 | → External ETCD Endpoints·Service·ServiceMonitor
  82 | → Prometheus ETCD Target UP
  83 | → Grafana datasource·Dashboard
  84 | → Member kubesphere-installer
  85 | → Member ClusterConfiguration
  86 | → external Monitoring 연결
  87 | → KubeSphere Platform Workload·Console·API 검증
  88 | → multicluster.clusterRole = member
  89 | → 기존 Host 접근·Join 대상 확인
  90 | → 보호된 Join 정보 전달
  91 | → Host Join
  92 | → Member Agent·Host-Member 연결 확인
  93 | → Host Console에서 신규 Member 정상
  94 | → Multi-Cluster 관리·관측 확인
  95 | → 전체 구축 최종 인수
  96 | ```
  97 | 
  98 | ### 반드시 분리할 성공
  99 | 
 100 | ```text
 101 | Monitoring Pod Running
 102 | ≠ Prometheus Target 정상
 103 | 
 104 | PVC Bound
 105 | ≠ Monitoring Pod Mount·데이터 사용 정상
 106 | 
 107 | Ingress 존재
 108 | ≠ Monitoring UI·VIP-B·HTTP 정상
 109 | 
 110 | Grafana UI 접속
 111 | ≠ Datasource·Query·Dashboard 정상
 112 | 
 113 | ETCD Service·Endpoints 존재
 114 | ≠ Prometheus ETCD Target UP
 115 | 
 116 | ks-installer Pod Running
 117 | ≠ KubeSphere 내부 설치 Task 성공
 118 | 
 119 | KubeSphere Console 열림
 120 | ≠ Member Role·external Monitoring·Storage·Platform Workload 정상
 121 | 
 122 | Host Console에 Cluster 이름 보임
 123 | ≠ Host-Member 연결과 Multi-Cluster 관리·관측 정상
 124 | ```
 125 | 
 126 | ## 3. 기준 문서
 127 | 
 128 | 1. [[30. 구축 및 전환/공통 구축/Xi'an/한국어/05-2|5.5.2 Install kubesphere - member cluster]]
 129 | 2. [[30. 구축 및 전환/Member 클러스터/개요|Member 클러스터 개요]]
 130 | 3. [[30. 구축 및 전환/Member 클러스터/05.2.1.1 Deploy preliminary components|Preliminary Components]]
 131 | 4. [[30. 구축 및 전환/Member 클러스터/05.2.1.2 Deploy CRDs|Prometheus Operator CRD]]
 132 | 5. [[30. 구축 및 전환/Member 클러스터/05.2.1.3 Deploy DKS kube-prometheus-stack components|DKS kube-prometheus-stack]]
 133 | 6. [[30. 구축 및 전환/Member 클러스터/05.2.1.4 Deploy Ingresses and External ETCD Monitoring|Monitoring Ingress·External ETCD Monitoring]]
 134 | 7. [[30. 구축 및 전환/Member 클러스터/05.2.1.5 Grafana Custom Dashboard Addition|Grafana Custom Dashboard]]
 135 | 8. [[30. 구축 및 전환/Member 클러스터/05.2.2 Install KubeSphere on Member Cluster|Member KubeSphere 설치]]
 136 | 9. [[40. 검증 및 인수/구축 검증 기준|구축 검증 기준]]
 137 | 10. [[60. 이슈 및 결정/장애/dev-apps-pa01-xas Monitoring 복붙 오적용|Monitoring 복붙 오적용 사례]]
 138 | 11. [[10. 기준 및 설계/클러스터 카탈로그/클러스터 카탈로그|Xi'an Cluster 카탈로그]]
 139 | 
 140 | 기존 Host 설치 문서는 비교·정상 기준일 뿐 9/3 적용 대상이 아니다.
 141 | 
 142 | ---
 143 | 
 144 | # Part 1. Preflight와 Preliminary Components
 145 | 
 146 | ## 4. 9/2 Storage Gate 재확인
 147 | 
 148 | Monitoring과 KubeSphere는 PVC와 StorageClass를 사용한다. 9/2 검증이 불완전하면 9/3 설치 실패를 KubeSphere 문제로 잘못 해석할 수 있다.
 149 | 
 150 | ### 4.1 재확인 항목
 151 | 
 152 | - Kubernetes API·Node·CNI·DNS 기본 기능 정상
 153 | - Trident Operator·Controller·Node Component 정상
 154 | - Backend `online`
 155 | - 승인된 StorageClass 존재
 156 | - Test PVC Bound
 157 | - Test Pod Mount 성공
 158 | - Container Write·Read·재읽기 성공
 159 | - 테스트 리소스 정리 결과 확인
 160 | - Monitoring PVC에 사용할 StorageClass·용량·Namespace 확정
 161 | - 역할별 Node에서 Storage 접근 차이 없음
 162 | 
 163 | ### 4.2 진행 금지 상태
 164 | 
 165 | - Backend `offline`
 166 | - StorageClass 실제값 미확정
 167 | - PVC Pending
 168 | - Pod `FailedMount`
 169 | - 특정 Infra Node에서만 Mount 실패
 170 | - Write·Read 실패
 171 | - Reclaim·정리 동작 미확인으로 데이터 삭제 위험 존재
 172 | 
 173 | 이 상태에서는 Monitoring Stack을 적용해 실패 원인을 더 복잡하게 만들지 않는다.
 174 | 
 175 | ## 5. 대상 Member Identity 고정
 176 | 
 177 | ### 5.1 가장 먼저 확인할 값
 178 | 
 179 | ```text
 180 | current-context
 181 | Cluster name
 182 | Stage
 183 | Node hostname·role·IP
 184 | VIP-A / VIP-B
 185 | Domain
 186 | StorageClass
 187 | Registry
 188 | External ETCD Endpoint
 189 | Monitoring Namespace
 190 | ```
 191 | 
 192 | ### 5.2 Cluster별 값 혼입 방지
 193 | 
 194 | Host·PRD Member·DEV Member는 다음 값이 다를 수 있다.
 195 | 
 196 | - ETCD Endpoint
 197 | - Certificate Secret과 Key 이름
 198 | - VIP-A·VIP-B
 199 | - Ingress Domain
 200 | - Cluster·Stage External Label
 201 | - StorageClass
 202 | - Registry Repository·Tag
 203 | - Node Selector·Taint
 204 | - Grafana Datasource
 205 | - KubeSphere external Monitoring Endpoint
 206 | 
 207 | Manifest가 적용됐다는 사실보다 **각 값이 현재 신규 Member Identity와 일치하는가**가 더 중요하다.
 208 | 
 209 | ### 5.3 기록 양식
 210 | 
 211 | ```text
 212 | 대상 Member Cluster: __________________________
 213 | current-context: ______________________________
 214 | Stage: _______________________________________
 215 | VIP-A / VIP-B: _______________________________
 216 | Domain: ______________________________________
 217 | StorageClass: _________________________________
 218 | Registry: ____________________________________
 219 | External ETCD: ________________________________
 220 | 확인 근거: ___________________________________
 221 | ```
 222 | 
 223 | 민감한 Endpoint 인증정보는 기록하지 않는다.
 224 | 
 225 | ## 6. Preliminary Components
 226 | 
 227 | ### 6.1 `monitoring` Namespace
 228 | 
 229 | Member custom Monitoring의 작업 경계다.
 230 | 
 231 | 완료 증거:
 232 | 
 233 | - Namespace가 `Active`
 234 | - 과거 `kubesphere-monitoring-system`과 혼동하지 않음
 235 | - 이후 CR·PVC·Secret·Service·Ingress가 올바른 Namespace에 생성됨
 236 | 
 237 | ### 6.2 ETCD Certificate Secret
 238 | 
 239 | External ETCD HTTPS Metric 접근에 필요한 인증 재료를 Prometheus에 제공한다.
 240 | 
 241 | 확인할 것:
 242 | 
 243 | - Secret 존재
 244 | - Namespace = `monitoring`
 245 | - Type
 246 | - 필요한 Key 이름 존재
 247 | - 실제 ETCD Certificate와 대응
 248 | - Secret 원문 미출력
 249 | - 파일·Key 권한과 전달 경로 승인
 250 | 
 251 | ```text
 252 | Secret 이름이 같음
 253 | ≠ 올바른 Cluster Certificate
 254 | ```
 255 | 
 256 | ### 6.3 Grafana·Prometheus·Alertmanager PVC
 257 | 
 258 | - StorageClass가 9/2 검증값과 일치한다.
 259 | - 요청 용량이 승인값과 Quota 안에 있다.
 260 | - PVC가 Bound된다.
 261 | - Pod가 실제 Mount한다.
 262 | - Node 배치와 NFS 접근이 정상이다.
 263 | 
 264 | Grafana PVC 하나만 보고 Prometheus·Alertmanager Storage를 자동 통과시키지 않는다.
 265 | 
 266 | ### 6.4 Preliminary 완료 Gate
 267 | 
 268 | ```text
 269 | monitoring Namespace Active
 270 | + Secret 구조 정상
 271 | + StorageClass 확정
 272 | + 필요한 PVC 생성 가능
 273 | + Registry 접근 가능
 274 | + Infra Node 배치 조건 확인
 275 | =
 276 | CRD와 Monitoring Stack 적용 가능
 277 | ```
 278 | 
 279 | ---
 280 | 
 281 | # Part 2. Prometheus Operator와 DKS Monitoring
 282 | 
 283 | ## 7. Prometheus Operator CRD
 284 | 
 285 | ### 7.1 CRD가 먼저인 이유
 286 | 
 287 | DKS custom Stack은 다음 API Kind를 사용한다.
 288 | 
 289 | - Prometheus
 290 | - Alertmanager
 291 | - ServiceMonitor
 292 | - PodMonitor
 293 | - PrometheusRule
 294 | - ThanosRuler 등 Bundle에 포함된 Kind
 295 | 
 296 | CRD가 없으면 Kubernetes API가 객체 종류를 해석할 수 없다.
 297 | 
 298 | ```text
 299 | CRD Applied
 300 | → Names Accepted
 301 | → Established
 302 | → API Discovery 가능
 303 | → Custom Resource 적용 가능
 304 | ```
 305 | 
 306 | ### 7.2 검증
 307 | 
 308 | - CRD 이름
 309 | - `Established=True`
 310 | - Version과 Served·Storage 상태
 311 | - 다른 Bundle Version과 충돌하지 않음
 312 | - Operator가 해당 CRD를 Watch할 준비가 됨
 313 | 
 314 | ```bash
 315 | kubectl get crd | grep monitoring.coreos.com
 316 | kubectl describe crd <crd-name>
 317 | ```
 318 | 
 319 | ### 7.3 흔한 실패
 320 | 
 321 | ```text
 322 | CRD Apply 명령 성공
 323 | ≠ Established 완료
 324 | 
 325 | 과거 CRD Version 잔존
 326 | → 새 Manifest Schema와 불일치 가능
 327 | 
 328 | Operator 먼저 기동
 329 | → 필요한 CRD가 없어 반복 실패
 330 | ```
 331 | 
 332 | ## 8. DKS custom kube-prometheus-stack
 333 | 
 334 | ### 8.1 핵심 구성요소
 335 | 
 336 | - Prometheus Operator
 337 | - Prometheus
 338 | - Alertmanager
 339 | - Grafana
 340 | - kube-state-metrics
 341 | - Node Exporter
 342 | - Kubernetes Component ServiceMonitor
 343 | - PrometheusRule
 344 | - 필요한 Adapter·Exporter
 345 | 
 346 | 정확한 목록은 현재 Bundle과 Manifest를 기준으로 확인한다.
 347 | 
 348 | ### 8.2 Cluster Identity
 349 | 
 350 | ```yaml
 351 | externalLabels:
 352 |   cluster: <current-member-cluster>
 353 |   stage: <current-stage>
 354 | ```
 355 | 
 356 | 이 Label은 Multi-Cluster Metric에서 출처를 구분한다. 다른 Cluster 이름을 복사하면 Pod는 Running이어도 Dashboard·Alert·Query가 잘못된 Identity를 표시한다.
 357 | 
 358 | ### 8.3 Storage
 359 | 
 360 | 확인할 것:
 361 | 
 362 | - Prometheus Retention과 PVC 용량
 363 | - StorageClass
 364 | - Alertmanager PVC
 365 | - Grafana PVC
 366 | - Volume Mount
 367 | - PVC·PV·Node·NFS 경로
 368 | 
 369 | ```text
 370 | PVC Bound
 371 | ≠ Prometheus가 정상 기동·데이터 기록
 372 | ```
 373 | 
 374 | ### 8.4 Node 배치
 375 | 
 376 | - `nodeSelector`
 377 | - `tolerations`
 378 | - `affinity` 또는 anti-affinity
 379 | - Replica 수
 380 | - 실제 Pod `NODE`
 381 | - Infra Node의 Taint
 382 | 
 383 | ```text
 384 | Manifest에 nodeSelector 존재
 385 | + Toleration 존재
 386 | + 실제 Pod가 대상 Infra Node
 387 | =
 388 | 배치 정책 적용 확인
 389 | ```
 390 | 
 391 | ### 8.5 Registry와 Image
 392 | 
 393 | - Registry FQDN
 394 | - Project·Repository
 395 | - Image Tag
 396 | - CA Trust
 397 | - Image Pull Secret 필요 여부
 398 | - Node에서 Pull 가능 여부
 399 | 
 400 | Image가 Pull되지 않으면 Monitoring 설정값을 먼저 바꾸지 않고 Pod Event를 확인한다.
 401 | 
 402 | ### 8.6 Stack 적용 후 검증
 403 | 
 404 | #### Kubernetes 객체
 405 | 
 406 | - Deployment·StatefulSet·DaemonSet
 407 | - Pod Ready·Restart
 408 | - Service·Endpoint
 409 | - PVC·PV
 410 | - CR 상태
 411 | - Event
 412 | 
 413 | #### 기능
 414 | 
 415 | - Prometheus Web/API
 416 | - Active Target
 417 | - Rule Load
 418 | - Alertmanager Cluster·Config
 419 | - Grafana Login·Datasource·Query
 420 | - Node·Kubernetes Metric 수집
 421 | 
 422 | ### 8.7 과잉 판정 방지
 423 | 
 424 | ```text
 425 | Operator Running
 426 | ≠ Prometheus CR Ready
 427 | 
 428 | Prometheus Pod Running
 429 | ≠ Target UP
 430 | 
 431 | Grafana Pod Running
 432 | ≠ Datasource 정상
 433 | 
 434 | Rule Object 존재
 435 | ≠ Prometheus가 Rule Load
 436 | 
 437 | Alertmanager Pod Running
 438 | ≠ Route·Receiver·알림 전달 정상
 439 | ```
 440 | 
 441 | ## 9. Monitoring Ingress와 VIP-B
 442 | 
 443 | ### 9.1 외부 요청 경로
 444 | 
 445 | ```text
 446 | 사용자 또는 운영자
 447 | → DNS / Monitoring FQDN
 448 | → Member VIP-B
 449 | → Router
 450 | → ingress-nginx-controller
 451 | → Monitoring Ingress
 452 | → Service
 453 | → Pod
 454 | ```
 455 | 
 456 | ### 9.2 확인할 값
 457 | 
 458 | - Hostname
 459 | - PRD/DEV·현재 Member Domain
 460 | - Path
 461 | - Service Name·Port
 462 | - Ingress Class
 463 | - TLS 방식
 464 | - Address
 465 | - DNS 해석
 466 | - VIP-B Backend
 467 | - Source 접근 조건
 468 | 
 469 | Host Cluster Domain이나 다른 Member VIP를 넣지 않는다.
 470 | 
 471 | ### 9.3 기능 검증
 472 | 
 473 | - DNS가 올바른 VIP-B로 해석된다.
 474 | - TCP 80/443 연결이 된다.
 475 | - Ingress Address가 Router와 일치한다.
 476 | - Backend Service·Endpoint가 존재한다.
 477 | - Prometheus·Grafana·Alertmanager UI 또는 API가 기대 상태를 반환한다.
 478 | - 인증·권한 정책이 의도와 일치한다.
 479 | 
 480 | ## 10. External ETCD Monitoring
 481 | 
 482 | ### 10.1 구조
 483 | 
 484 | Member의 Kubernetes ETCD가 External Node에서 실행되는 경우 Kubernetes Pod Selector로 직접 발견되지 않는다. Kubernetes 객체로 Endpoint를 표현하고 ServiceMonitor가 이를 Scrape하도록 연결한다.
 485 | 
 486 | ```text
 487 | 실제 ETCD Node IP:Port
 488 | → Kubernetes Endpoints / EndpointSlice
 489 | → Headless Service
 490 | → ServiceMonitor
 491 | → Prometheus
 492 | → /metrics HTTPS
 493 | → Target UP
 494 | ```
 495 | 
 496 | ### 10.2 Endpoints
 497 | 
 498 | 확인할 것:
 499 | 
 500 | - 현재 Member의 실제 ETCD Node IP
 501 | - Port·Name
 502 | - Address 개수
 503 | - 다른 Cluster IP 혼입 여부
 504 | - TLS Server Name 또는 Metric Path 요구
 505 | 
 506 | ### 10.3 Service
 507 | 
 508 | - Selector 없는 Headless 또는 승인된 구조
 509 | - Port Name이 ServiceMonitor와 일치
 510 | - Endpoint 연결
 511 | - Namespace 일치
 512 | 
 513 | ### 10.4 ServiceMonitor
 514 | 
 515 | - Namespace Selector
 516 | - Service Label Selector
 517 | - Port Name
 518 | - Scheme = HTTPS 등 실제값
 519 | - TLS Config
 520 | - Secret Key 참조
 521 | - Scrape Interval
 522 | 
 523 | ### 10.5 최종 Target
 524 | 
 525 | ```text
 526 | Service·Endpoints 존재
 527 | ≠ Scrape 성공
 528 | ```
 529 | 
 530 | Prometheus Target에서 확인한다.
 531 | 
 532 | - Health = `UP`
 533 | - Last Scrape
 534 | - Scrape Duration
 535 | - Error 없음
 536 | - Endpoint가 현재 Member ETCD
 537 | - Metric이 실제로 Query됨
 538 | 
 539 | ### 10.6 Target Down 분기
 540 | 
 541 | | 증상 | 첫 확인 |
 542 | |---|---|
 543 | | No Endpoint | Endpoints·Service Label |
 544 | | Connection refused | ETCD Metric Listen·Port |
 545 | | Timeout | Network·Route·Firewall |
 546 | | x509 | CA·Client Certificate·Server Name |
 547 | | 403/401 | ETCD Auth·Certificate |
 548 | | Wrong Cluster Metric | Endpoints IP·External Label |
 549 | 
 550 | ## 11. Monitoring 복붙 오적용 방지
 551 | 
 552 | ### 11.1 실제 학습 사례
 553 | 
 554 | 과거 DEV Member에서 다음과 같은 값 혼입이 발생했다.
 555 | 
 556 | - Host ETCD Endpoint를 Member에 적용
 557 | - Grafana Datasource Namespace를 잘못 적용
 558 | - 일부 Pod·PVC·Ingress는 정상
 559 | - ETCD Target과 Grafana Data는 실패
 560 | 
 561 | ### 11.2 핵심 교훈
 562 | 
 563 | ```text
 564 | 리소스 개수가 많이 Running
 565 | 보다
 566 | 각 Endpoint·Datasource·Label이 현재 Cluster Identity와 일치
 567 | 가 더 강한 정상 판정
 568 | ```
 569 | 
 570 | ### 11.3 Manifest 검토표
 571 | 
 572 | | 값 | 현재 Member 근거 | 다른 Cluster 값 혼입 여부 |
 573 | |---|---|---|
 574 | | externalLabels.cluster | Cluster 카탈로그·context |  |
 575 | | externalLabels.stage | 승인 Stage |  |
 576 | | ETCD Endpoints | 실제 Member ETCD |  |
 577 | | StorageClass | 9/2 검증 |  |
 578 | | Ingress Host | 현재 Member Domain |  |
 579 | | Grafana Datasource | `monitoring` Service |  |
 580 | | Registry·Tag | 현재 Bundle |  |
 581 | | Node Selector | 현재 Node Role |  |
 582 | 
 583 | ---
 584 | 
 585 | # Part 3. Grafana와 Monitoring 인수
 586 | 
 587 | ## 12. Grafana Datasource
 588 | 
 589 | ### 12.1 용도
 590 | 
 591 | Grafana가 Metric Query를 보낼 Prometheus Service를 지정한다.
 592 | 
 593 | 기존 구조 예:
 594 | 
 595 | ```text
 596 | Grafana Datasource
 597 | → http://prometheus-k8s.monitoring.svc:9090
 598 | ```
 599 | 
 600 | 실제 Service 이름·Namespace는 현재 Manifest에서 확인한다.
 601 | 
 602 | ### 12.2 KubeSphere external Monitoring Endpoint와 구분
 603 | 
 604 | ```text
 605 | Grafana Datasource
 606 | → Grafana가 Query할 Prometheus Service
 607 | 
 608 | KubeSphere external Monitoring Endpoint
 609 | → KubeSphere가 외부 Monitoring으로 사용할 Prometheus Service
 610 | ```
 611 | 
 612 | 기존 문서 구조에서는 다음처럼 서로 다른 Service를 사용할 수 있다.
 613 | 
 614 | ```text
 615 | prometheus-k8s.monitoring.svc
 616 | vs
 617 | prometheus-operated.monitoring.svc
 618 | ```
 619 | 
 620 | 이름을 암기해 서로 바꾸지 않고 실제 Service·Port·목적을 확인한다.
 621 | 
 622 | ### 12.3 검증
 623 | 
 624 | - Datasource URL
 625 | - Access Mode
 626 | - Save & Test 성공
 627 | - 간단 Query 결과
 628 | - Cluster Label
 629 | - Dashboard Data 시간 범위
 630 | - 다른 Cluster Metric 혼입 없음
 631 | 
 632 | ## 13. Dashboard
 633 | 
 634 | ### 13.1 Dashboard 추가
 635 | 
 636 | - 승인된 JSON 또는 ConfigMap
 637 | - UID·Title 중복
 638 | - Datasource 참조
 639 | - Variable·Cluster Label
 640 | - Version
 641 | - Import 결과
 642 | 
 643 | ### 13.2 기능 검증
 644 | 
 645 | - Node·Pod·Cluster Metric 표시
 646 | - 현재 Member 이름 표시
 647 | - 최근 Data 존재
 648 | - Panel Error 없음
 649 | - Datasource Query 성공
 650 | - 실제 Kubernetes 상태와 대략 일치
 651 | 
 652 | ### 13.3 과잉 판정 방지
 653 | 
 654 | ```text
 655 | Dashboard 화면 열림
 656 | ≠ Panel Query 정상
 657 | 
 658 | 일부 Panel 값 있음
 659 | ≠ 현재 Member Metric
 660 | 
 661 | Datasource Save & Test 성공
 662 | ≠ 모든 Dashboard Variable 정상
 663 | ```
 664 | 
 665 | ## 14. Monitoring 최종 Gate
 666 | 
 667 | 다음이 모두 충족되어야 Member KubeSphere 설치로 진행한다.
 668 | 
 669 | 1. Monitoring Namespace·Secret·PVC 정상
 670 | 2. Prometheus CRD Established
 671 | 3. Operator·Prometheus·Alertmanager·Grafana 정상
 672 | 4. PVC Mount·Storage 사용 정상
 673 | 5. Node 배치 정책 정상
 674 | 6. Prometheus 주요 Target 정상
 675 | 7. External ETCD Target `UP`
 676 | 8. Rule Load 정상
 677 | 9. Grafana Datasource·Query 정상
 678 | 10. Monitoring Ingress·VIP-B 정상
 679 | 11. Cluster·Stage Label 현재 Member와 일치
 680 | 12. 민감정보 노출 없음
 681 | 
 682 | ### 14.1 중단 기준
 683 | 
 684 | - ETCD Target Down 원인 미확정
 685 | - Grafana가 다른 Cluster Prometheus를 참조
 686 | - PVC Mount 실패
 687 | - Registry Image Pull 실패
 688 | - CRD Version 충돌
 689 | - 주요 Monitoring Pod 반복 재시작
 690 | - Ingress가 다른 Member Domain/VIP 사용
 691 | - External Label 잘못 적용
 692 | 
 693 | ---
 694 | 
 695 | # Part 4. Member KubeSphere
 696 | 
 697 | ## 15. Member installer와 ClusterConfiguration
 698 | 
 699 | ### 15.1 두 파일의 역할
 700 | 
 701 | ```text
 702 | kubesphere-installer.yaml
 703 | → Installer CRD·RBAC·Deployment와 실행기
 704 | 
 705 | cluster-configure.yaml / ClusterConfiguration
 706 | → 실제 KubeSphere 기능·환경·Role·Monitoring·Storage·Registry 설정
 707 | ```
 708 | 
 709 | ### 15.2 Member 핵심값
 710 | 
 711 | - 대상 Member context
 712 | - StorageClass
 713 | - Registry·Image
 714 | - External ETCD
 715 | - Monitoring Type = external 등 승인값
 716 | - External Prometheus Endpoint
 717 | - `multicluster.clusterRole = member`
 718 | - Console·Ingress
 719 | - Node Selector·Toleration
 720 | - Module Enable·Disable
 721 | - Host 연결에 필요한 보호된 값
 722 | 
 723 | ### 15.3 Host와 Member 차이
 724 | 
 725 | | 항목 | Host | 신규 Member |
 726 | |---|---|---|
 727 | | 역할 | 중앙 Multi-Cluster 관리 | 사용자 Workload·Member 실행 |
 728 | | clusterRole | `host` | `member` |
 729 | | Monitoring | Host 기준 구성 | DKS custom external Monitoring 사용 |
 730 | | Join | Member를 받음 | 기존 Host에 Join |
 731 | | 이번 출장 | 재설치 없음 | 신규 설치 대상 |
 732 | 
 733 | Host Manifest를 복사해 `clusterRole`만 바꾸는 방식으로 적용하지 않는다.
 734 | 
 735 | ## 16. Installer 로그
 736 | 
 737 | ### 16.1 먼저 구분할 것
 738 | 
 739 | ```text
 740 | ks-installer Pod 자체가 Pending·Crash인가?
 741 | vs
 742 | Installer는 Running이지만 내부 Task가 실패하는가?
 743 | ```
 744 | 
 745 | ### 16.2 Task 범주
 746 | 
 747 | - common
 748 | - monitoring
 749 | - multicluster
 750 | - network
 751 | - openpitrix
 752 | - devops
 753 | - logging·events·alerting 등 Bundle 구성
 754 | 
 755 | 정확한 Task는 현재 로그를 기준으로 본다.
 756 | 
 757 | ### 16.3 실패 시 확인
 758 | 
 759 | | 실패 범주 | 먼저 확인 |
 760 | |---|---|
 761 | | Pod Pending | Node Selector·Taint·PVC·Image |
 762 | | ImagePullBackOff | Registry·Tag·CA·Secret |
 763 | | CRD not found | CRD 적용·Established |
 764 | | Monitoring Task | External Endpoint·Service·CRD·PVC |
 765 | | Multicluster Task | Role·Join 설정·보호된 값 |
 766 | | Timeout | API·Network·Webhook·Resource |
 767 | 
 768 | ### 16.4 완료 증거
 769 | 
 770 | - Installer Task 성공
 771 | - KubeSphere 주요 Deployment·StatefulSet Ready
 772 | - Console/API 접근
 773 | - `clusterRole=member`
 774 | - External Monitoring Endpoint 정상
 775 | - Storage PVC 정상
 776 | - Platform Workload 배치 정상
 777 | - Installer 종료·Replica 정책이 Manual과 일치
 778 | 
 779 | ## 17. Platform Workload 배치
 780 | 
 781 | ### 17.1 확인 요소
 782 | 
 783 | - Node Label
 784 | - Node Taint
 785 | - Workload Node Selector
 786 | - Toleration
 787 | - Replica 수
 788 | - 실제 Pod `NODE`
 789 | - Pod Disruption·Anti-affinity
 790 | 
 791 | ### 17.2 완료 판단
 792 | 
 793 | ```text
 794 | Manifest에 배치 조건 있음
 795 | + Scheduler Event 정상
 796 | + 실제 새 Pod가 Infra Node에 배치
 797 | + Replica가 역할별 Node에 분산
 798 | =
 799 | DKS 배치 정책 반영
 800 | ```
 801 | 
 802 | ### 17.3 Pending 분기
 803 | 
 804 | ```text
 805 | 원인을 KubeSphere 자체 오류로 단정하지 않음
 806 | → nodeSelector와 실제 Label
 807 | → Taint와 Toleration
 808 | → PVC Binding
 809 | → Resource Request
 810 | → Scheduler Event
 811 | ```
 812 | 
 813 | ## 18. Member 자체 Pre-Join 검증
 814 | 
 815 | Host Join 전에 Member가 자체적으로 정상이어야 한다.
 816 | 
 817 | ### 18.1 Kubernetes
 818 | 
 819 | - API·Node·Control Plane·CNI·DNS
 820 | - Ingress Controller
 821 | - Event에 미해결 Critical Error 없음
 822 | 
 823 | ### 18.2 Storage
 824 | 
 825 | - Trident·Backend·StorageClass
 826 | - Monitoring·KubeSphere PVC Mount
 827 | - Write·Read
 828 | 
 829 | ### 18.3 Monitoring
 830 | 
 831 | - Prometheus·Alertmanager·Grafana
 832 | - External ETCD Target `UP`
 833 | - Datasource·Dashboard
 834 | - Ingress·HTTP
 835 | 
 836 | ### 18.4 KubeSphere
 837 | 
 838 | - Installer Task
 839 | - Console·API
 840 | - 주요 Platform Workload
 841 | - `clusterRole=member`
 842 | - External Monitoring 연결
 843 | - Infra 배치
 844 | 
 845 | ### 18.5 Network·Identity
 846 | 
 847 | - Member VIP-A·VIP-B
 848 | - Domain
 849 | - Existing Host와 필요한 통신
 850 | - DNS·Firewall
 851 | - Cluster Name·Stage·External Label
 852 | 
 853 | ### 18.6 Pre-Join Gate
 854 | 
 855 | 위 항목 중 하나라도 Member 자체 장애가 남아 있으면 Join으로 문제를 덮지 않는다.
 856 | 
 857 | ---
 858 | 
 859 | # Part 5. 기존 Host Join
 860 | 
 861 | ## 19. Join의 의미
 862 | 
 863 | Host Join은 Console 목록에 이름을 추가하는 UI 작업이 아니다.
 864 | 
 865 | ```text
 866 | Member KubeSphere = member로 준비
 867 | + 기존 Host = host로 정상
 868 | + 필요한 인증정보를 안전하게 공유
 869 | + Host↔Member Network·DNS·API 통신
 870 | + Member Agent·연결 Component 정상
 871 | =
 872 | Host가 신규 Member를 관리·관측할 수 있는 Multi-Cluster 연결
 873 | ```
 874 | 
 875 | ## 20. Join 전 기존 Host 확인
 876 | 
 877 | 기존 Host에는 변경을 최소화하고 다음을 조회한다.
 878 | 
 879 | - Host Console·API 접근
 880 | - Host `clusterRole=host`
 881 | - 기존 PRD·DEV Member 상태
 882 | - 신규 Member 이름 중복 여부
 883 | - Join 대상 Workspace·Cluster 관리 권한
 884 | - Host Resource 상태
 885 | - Multi-Cluster Component 상태
 886 | - Host↔신규 Member DNS·Network·Firewall
 887 | - Join 승인자와 보호된 값 전달 방법
 888 | 
 889 | 기존 Host에 문제가 있으면 신규 Member Join 실패와 분리한다.
 890 | 
 891 | ## 21. 보호된 Join 정보
 892 | 
 893 | ### 21.1 원칙
 894 | 
 895 | - Secret·JWT·kubeconfig 원문을 문서에 복사하지 않는다.
 896 | - 화면 공유 시 Masking한다.
 897 | - 승인된 전달 경로를 사용한다.
 898 | - 전달 대상과 유효시간을 확인한다.
 899 | - 사용 후 임시 파일·Clipboard·Shell History를 정리한다.
 900 | - 파일 권한은 최소화한다.
 901 | 
 902 | ### 21.2 기록할 수 있는 정보
 903 | 
 904 | - 값의 종류
 905 | - 발급·확인 시각
 906 | - 전달자·수신자 역할
 907 | - 저장 위치가 아닌 승인된 관리체계
 908 | - 사용 성공 여부
 909 | - Rotation·폐기 필요 여부
 910 | 
 911 | ## 22. Join 실행 흐름
 912 | 
 913 | 실제 UI·명령·Manifest는 현재 Manual과 Host Console을 따른다.
 914 | 
 915 | ```text
 916 | 신규 Member Name·Role 확인
 917 | → 기존 Host의 Add / Import / Join 경로 확인
 918 | → 보호된 연결정보 준비
 919 | → Join 적용
 920 | → Member Agent·연결 Workload 생성
 921 | → Host Console에서 Cluster 등록
 922 | → 상태 전환 관찰
 923 | → API·Resource·Monitoring 관리·관측 확인
 924 | ```
 925 | 
 926 | ### 22.1 이름과 Identity
 927 | 
 928 | - Cluster Name이 현재 Member와 일치
 929 | - PRD·DEV·Stage Tag 일치
 930 | - 기존 Cluster와 중복 없음
 931 | - 잘못된 과거 이름 사용 금지
 932 | 
 933 | ### 22.2 Network
 934 | 
 935 | - Host에서 Member API 접근
 936 | - Member에서 Host 연결 Endpoint 접근
 937 | - DNS 해석
 938 | - TLS 인증
 939 | - 필요한 Port
 940 | - Proxy·Firewall 영향
 941 | 
 942 | ### 22.3 Agent·Component
 943 | 
 944 | - Member Agent Pod
 945 | - Host 측 Multi-Cluster Component
 946 | - Registration 상태
 947 | - Log·Event
 948 | - Restart·Error
 949 | 
 950 | ## 23. Join 완료 증거
 951 | 
 952 | ```text
 953 | Host Console에 신규 Member 표시
 954 | + Status 정상
 955 | + Cluster Name·Stage 정확
 956 | + Member Node·Namespace·Workload 조회 가능
 957 | + Member KubeSphere 자체 Console·API 정상
 958 | + Host에서 Member Monitoring 정보 확인 가능
 959 | + Host-Member 연결 Component 정상
 960 | + 기존 Member 영향 없음
 961 | + 권한 경계 정상
 962 | ```
 963 | 
 964 | ### 23.1 단순 목록 표시를 넘어 확인할 것
 965 | 
 966 | - Node 수와 Role이 Member 실제 상태와 일치
 967 | - Namespace·Project 조회
 968 | - Workload 상태
 969 | - Monitoring Metric의 Cluster Label
 970 | - Host에서 선택한 Cluster가 올바름
 971 | - Member의 API·Network Error 없음
 972 | - 기존 PRD·DEV Member 상태 변화 없음
 973 | 
 974 | ## 24. Join 실패 분기
 975 | 
 976 | ### 24.1 Host Console에 Cluster가 안 보임
 977 | 
 978 | - Join 요청이 생성됐는가
 979 | - Cluster Name·Identity 중복
 980 | - Host 권한
 981 | - 보호된 값 유효성
 982 | - Host API·Component Log
 983 | 
 984 | ### 24.2 Cluster는 보이지만 상태 이상
 985 | 
 986 | ```text
 987 | Member 자체 정상인가?
 988 | → Member Agent 정상인가?
 989 | → Host→Member API 통신이 되는가?
 990 | → DNS·TLS·Firewall은 정상인가?
 991 | → 인증정보가 현재 Member 것인가?
 992 | ```
 993 | 
 994 | ### 24.3 Resource는 보이지만 Monitoring 없음
 995 | 
 996 | - Member external Monitoring 정상
 997 | - Cluster External Label
 998 | - Host가 참조하는 Metric Source
 999 | - Datasource·Endpoint
1000 | - Multi-Cluster Monitoring Component
1001 | 
1002 | ### 24.4 기존 Member까지 영향
1003 | 
1004 | 즉시 신규 Join 작업과 영향 관계를 확인하고, 추가 변경을 멈춘다. Host 공통 Component·Config 변경이 있었는지 비교한다.
1005 | 
1006 | ---
1007 | 
1008 | # Part 6. 전체 구축 최종 인수
1009 | 
1010 | ## 25. 8/31~9/3 구축 흐름 복원
1011 | 
1012 | ```text
1013 | 8/31
1014 | 신규 Member VM·LB·Bastion·Node 실제값 확인
1015 | → Pre-setting
1016 | → Inventory·변수
1017 | → Ansible 연결
1018 | 
1019 | 9/1
1020 | Kubespray
1021 | → API·Node·System Pod·CNI·DNS·ETCD·Runtime 검증
1022 | 
1023 | 9/2
1024 | Snapshotter·Trident·Backend·StorageClass
1025 | → PVC·PV
1026 | → Pod Mount
1027 | → Write·Read
1028 | 
1029 | 9/3
1030 | Member Monitoring
1031 | → Member KubeSphere
1032 | → 기존 Host Join
1033 | → Multi-Cluster 최종 인수
1034 | ```
1035 | 
1036 | ## 26. 기능별 인수 매트릭스
1037 | 
1038 | | 영역 | 확인 대상 | 최소 증거 | 판정 |
1039 | |---|---|---|---|
1040 | | VM·Node | 역할·CPU·Memory·Disk·NIC | 승인 설계·현재 출력 |  |
1041 | | Bastion | SSH·sudo·Bundle·Repo | 연결·Version |  |
1042 | | Inventory | Host·Group·VIP·CIDR·Domain | 기준본·대조표 |  |
1043 | | Kubespray | Task·Recap | 미해결 실패 없음 |  |
1044 | | Kubernetes API | VIP-A·readyz | API 응답 |  |
1045 | | Node | Ready·Role·Version | Node 출력 |  |
1046 | | CNI·DNS | Calico·CoreDNS | Pod·기능 테스트 |  |
1047 | | Storage | Backend·SC·PVC·Mount·RW | 단계별 증적 |  |
1048 | | Monitoring | Pod·Target·Rule·Datasource | ETCD UP·Query |  |
1049 | | Monitoring Ingress | DNS·VIP-B·HTTP | 응답·Backend |  |
1050 | | Member KubeSphere | Task·Console·API·Role | Member 기능 |  |
1051 | | 배치 | Infra Node·Toleration | 실제 Pod NODE |  |
1052 | | Host Join | Cluster 상태·Agent | Multi-Cluster 상태 |  |
1053 | | 회귀 | 기존 Host·Member | 영향 없음 |  |
1054 | | 보안 | Secret·Token·Key | 미노출·정리 |  |
1055 | 
1056 | ## 27. 최종 완료 조건
1057 | 
1058 | ### 27.1 신규 Member 자체
1059 | 
1060 | - Kubernetes API·Node·CNI·DNS 정상
1061 | - Storage Mount·Write/Read 정상
1062 | - Monitoring 주요 Component 정상
1063 | - External ETCD Target `UP`
1064 | - Grafana Datasource·Dashboard 정상
1065 | - Member KubeSphere Console·API 정상
1066 | - `clusterRole=member`
1067 | - Platform Workload 배치 정상
1068 | - 주요 Ingress·VIP-B 정상
1069 | 
1070 | ### 27.2 기존 Host Join
1071 | 
1072 | - Host 접근·Role 정상
1073 | - 신규 Member Join 성공
1074 | - Host Console Status 정상
1075 | - Member Resource 조회·관리 가능
1076 | - Member Monitoring 관측 가능
1077 | - 기존 Member 영향 없음
1078 | 
1079 | ### 27.3 인수·기록
1080 | 
1081 | - 환경 실제값과 기준본 차이 기록
1082 | - 실행 로그·검증 증적 위치 기록
1083 | - 미완료·Blocker 구분
1084 | - 보호된 값 정리
1085 | - 현지 담당자에게 문서 위치와 정상 기준 전달
1086 | - 9/4 철수 문서에 인계 항목 반영
1087 | 
1088 | ## 28. 부분 완료·보류 판정
1089 | 
1090 | ### Pass
1091 | 
1092 | 모든 핵심 완료 조건을 통과하고 잔여 항목이 비차단적이다.
1093 | 
1094 | ### Partial Pass
1095 | 
1096 | 핵심 기능은 정상이나 문서 정리·부가 Dashboard·비차단 Q&A 등이 남았다. 남은 항목의 영향·담당자·기한이 명확해야 한다.
1097 | 
1098 | ### Blocked
1099 | 
1100 | 다음 중 하나라도 남으면 최종 완료로 선언하지 않는다.
1101 | 
1102 | - Kubernetes 기본 기능 비정상
1103 | - Storage Mount·Write/Read 실패
1104 | - External ETCD Target Down
1105 | - Member KubeSphere 핵심 Task 실패
1106 | - `clusterRole` 또는 Cluster Identity 오류
1107 | - Host Join 실패
1108 | - Host Console Member 상태 이상
1109 | - 기존 Cluster 영향 발생
1110 | - 보호된 값 노출·통제 미확정
1111 | 
1112 | ## 29. 잔여 항목 기록
1113 | 
1114 | | 항목 | 현재 통과 지점 | 최초 실패·미확인 지점 | 영향 | 다음 확인 | 담당 영역 | 상태 |
1115 | |---|---|---|---|---|---|---|
1116 | |  |  |  |  |  |  |  |
1117 | 
1118 | `완료`, `비차단 잔여`, `차단`, `외부 확인`을 구분한다. 실패를 질문 목록으로만 남기고 완료 처리하지 않는다.
1119 | 
1120 | ## 30. 최종 증적 패킷
1121 | 
1122 | ### 30.1 포함할 것
1123 | 
1124 | - 대상 Member Identity·context 확인
1125 | - Node·System Pod·API 검증
1126 | - Storage Backend·SC·PVC·Mount·RW
1127 | - Monitoring Component·Target·Datasource
1128 | - KubeSphere Task·Workload·Console
1129 | - Host Join·Cluster 상태
1130 | - 기존 Cluster 회귀 확인
1131 | - 질문·결정·잔여 항목
1132 | 
1133 | ### 30.2 포함하지 않을 것
1134 | 
1135 | - Secret Data
1136 | - Token
1137 | - Password
1138 | - Private Key
1139 | - kubeconfig 원문
1140 | - JWT
1141 | - 보호된 Join 값
1142 | - 인증서 원문
1143 | 
1144 | ### 30.3 증적 파일 규칙
1145 | 
1146 | - 날짜·대상 Cluster·영역을 파일명에 표시
1147 | - Dynamic Pod 이름·시간이 현재 실행임을 명시
1148 | - Screenshot은 민감정보 Masking
1149 | - 참조 출력과 실제 실행 증적 구분
1150 | - 원본 로그와 요약 판단을 분리
1151 | 
1152 | ---
1153 | 
1154 | # Part 7. 강사·교육생 학습과 훈련
1155 | 
1156 | ## 31. 숙지 수준 분류
1157 | 
1158 | ### A. 문서 없이 설명할 것
1159 | 
1160 | - [ ] Member Monitoring을 KubeSphere보다 먼저 구성하는 이유
1161 | - [ ] Namespace·Secret·PVC·CRD의 선후관계
1162 | - [ ] Prometheus CRD `Established`의 의미
1163 | - [ ] External Label이 Cluster별이어야 하는 이유
1164 | - [ ] Monitoring Ingress와 VIP-B 경로
1165 | - [ ] ETCD Endpoint→Service→ServiceMonitor→Target 관계
1166 | - [ ] Target `UP`이 최종 증거인 이유
1167 | - [ ] Grafana Datasource와 KubeSphere external Monitoring Endpoint 차이
1168 | - [ ] installer와 ClusterConfiguration 차이
1169 | - [ ] Member `clusterRole=member` 의미
1170 | - [ ] 기존 Host를 재설치하지 않는 이유
1171 | - [ ] Host Join이 Multi-Cluster에서 완성하는 것
1172 | - [ ] 목록 표시와 실제 Multi-Cluster 정상의 차이
1173 | - [ ] 8/31~9/3 전체 구축의 Gate
1174 | 
1175 | ### B. 문서를 보며 정확히 수행·설명할 것
1176 | 
1177 | - [ ] Preliminary Components 적용·확인
1178 | - [ ] Secret Key 존재를 원문 노출 없이 확인
1179 | - [ ] CRD 적용·Established 확인
1180 | - [ ] custom Stack Manifest 핵심값 검토
1181 | - [ ] PVC·Pod·Node 배치 확인
1182 | - [ ] Monitoring Ingress·Service·Endpoint 확인
1183 | - [ ] ETCD Service·Endpoints·ServiceMonitor 확인
1184 | - [ ] Prometheus Target 확인
1185 | - [ ] Grafana Datasource·Dashboard 확인
1186 | - [ ] Member installer·ClusterConfiguration 검토
1187 | - [ ] Installer Task·Workload·Role 검증
1188 | - [ ] 기존 Host Join 절차와 상태 확인
1189 | - [ ] 최종 인수 매트릭스 작성
1190 | 
1191 | ### C. 현장에서 반드시 다시 확인할 것
1192 | 
1193 | - 신규 Member Cluster Name·Stage·context
1194 | - Node·VIP·Domain
1195 | - StorageClass
1196 | - ETCD IP·Port·Certificate Key 이름
1197 | - Registry·Image Tag
1198 | - Monitoring PVC 용량
1199 | - Ingress FQDN
1200 | - Grafana·KubeSphere Prometheus Endpoint
1201 | - Join 대상 Host와 Cluster Name
1202 | - 보호된 값 전달 방식
1203 | - 기존 Host·Member 현재 상태
1204 | - 승인자·담당자·인계 대상
1205 | 
1206 | ## 32. 자가점검
1207 | 
1208 | | 질문 | 상태 | 막힌 부분 | 돌아갈 문서 |
1209 | |---|---|---|---|
1210 | | Monitoring 전체 순서를 10분 안에 설명하는가? | 미평가 |  | 05-2 |
1211 | | CRD와 Custom Resource 선후를 설명하는가? | 미평가 |  | 05.2.1.2 |
1212 | | Cluster별 Identity 혼입 위험을 설명하는가? | 미평가 |  | Monitoring 사례 |
1213 | | ETCD Target Down 분기를 설명하는가? | 미평가 |  | 05.2.1.4 |
1214 | | 두 Prometheus Endpoint를 구분하는가? | 미평가 |  | 05-2 |
1215 | | Member installer Task를 읽는가? | 미평가 |  | 05.2.2 |
1216 | | `clusterRole=member`를 확인하는가? | 미평가 |  | 05.2.2 |
1217 | | Join 전 Member 자체 Gate를 설명하는가? | 미평가 |  | 이 문서 §18 |
1218 | | 기존 Host Join의 보호된 값 경계를 설명하는가? | 미평가 |  | 이 문서 §21 |
1219 | | Host Console 목록 이상으로 검증하는가? | 미평가 |  | 이 문서 §23 |
1220 | | 전체 구축 Pass·Partial·Blocked를 구분하는가? | 미평가 |  | 이 문서 §28 |
1221 | 
1222 | ## 33. 직접 연습
1223 | 
1224 | ### 연습 1 — Member 전체 순서 15분 설명
1225 | 
1226 | ```text
1227 | Storage Gate
1228 | → Preliminary Components
1229 | → CRD
1230 | → custom Monitoring
1231 | → Ingress
1232 | → ETCD Target
1233 | → Grafana
1234 | → Member KubeSphere
1235 | → Pre-Join
1236 | → Existing Host Join
1237 | → Multi-Cluster
1238 | → Final Acceptance
1239 | ```
1240 | 
1241 | 각 단계에서 다음을 말한다.
1242 | 
1243 | ```text
1244 | 왜 필요한가?
1245 | 무엇을 입력하는가?
1246 | 성공 증거는 무엇인가?
1247 | 어디서 멈추는가?
1248 | ```
1249 | 
1250 | ### 연습 2 — Cluster 값 혼입 찾기
1251 | 
1252 | Host·PRD Member·DEV Member 자료에서 다음 값을 섞은 Manifest를 만들고 잘못된 항목을 찾는다.
1253 | 
1254 | ```text
1255 | externalLabels.cluster
1256 | ETCD Endpoints
1257 | StorageClass
1258 | Ingress Host
1259 | Grafana Datasource
1260 | KubeSphere Monitoring Endpoint
1261 | clusterRole
1262 | ```
1263 | 
1264 | ### 연습 3 — ETCD Monitoring 그림
1265 | 
1266 | ```text
1267 | ETCD Node
1268 | → Endpoints
1269 | → Service
1270 | → ServiceMonitor
1271 | → Prometheus
1272 | → Target UP
1273 | → Query
1274 | ```
1275 | 
1276 | 각 객체가 존재하지만 Target이 Down일 수 있는 이유를 설명한다.
1277 | 
1278 | ### 연습 4 — Monitoring 실패 카드
1279 | 
1280 | ```text
1281 | A. CRD 없음
1282 | B. Prometheus Pod Pending + PVC Pending
1283 | C. Pod Running + ETCD Target Down
1284 | D. Grafana 열림 + Datasource Error
1285 | E. Ingress 존재 + DNS 다른 VIP
1286 | ```
1287 | 
1288 | 첫 단절과 다음 확인을 고른다.
1289 | 
1290 | ### 연습 5 — Installer 로그 카드
1291 | 
1292 | 다음 실패를 분류한다.
1293 | 
1294 | ```text
1295 | ImagePullBackOff
1296 | CRD not found
1297 | Monitoring endpoint timeout
1298 | clusterRole mismatch
1299 | Pod Pending on tainted Infra Node
1300 | ```
1301 | 
1302 | ### 연습 6 — Join Preflight
1303 | 
1304 | ```text
1305 | Member Kubernetes:
1306 | Member Storage:
1307 | Member Monitoring:
1308 | Member KubeSphere:
1309 | Member Identity:
1310 | Existing Host:
1311 | Network/DNS/TLS:
1312 | Protected Join Data:
1313 | ```
1314 | 
1315 | 하나라도 미확정이면 어떤 영향이 있는지 말한다.
1316 | 
1317 | ### 연습 7 — Multi-Cluster 판정
1318 | 
1319 | Host Console에서 Cluster 이름만 보이는 화면과 다음 증적을 비교한다.
1320 | 
1321 | - Status
1322 | - Node·Namespace·Workload
1323 | - Monitoring Metric
1324 | - Agent Pod
1325 | - API Connectivity
1326 | - 기존 Member 상태
1327 | 
1328 | 목록 표시만으로 완료할 수 없는 이유를 설명한다.
1329 | 
1330 | ### 연습 8 — 최종 인수 매트릭스
1331 | 
1332 | 8/31~9/3의 실제 또는 가상 증적을 기능별 인수 표에 넣고 Pass·Partial·Blocked를 판정한다.
1333 | 
1334 | ## 34. 대표 문제 상황
1335 | 
1336 | ### 사례 1 — Monitoring Pod 정상, ETCD Target Down
1337 | 
1338 | ```text
1339 | 확인된 사실
1340 | → Stack은 기동
1341 | → ETCD Scrape만 실패
1342 | 
1343 | 다음 확인
1344 | → Endpoints가 현재 Member ETCD IP인가?
1345 | ```
1346 | 
1347 | ### 사례 2 — Grafana 열림, Data 없음
1348 | 
1349 | ```text
1350 | UI 접속과 Datasource 성공 분리
1351 | → Datasource URL
1352 | → Prometheus Service·Endpoint
1353 | → Save & Test
1354 | → Query
1355 | → Cluster Label
1356 | ```
1357 | 
1358 | ### 사례 3 — KubeSphere Monitoring Task 실패
1359 | 
1360 | ```text
1361 | Storage PVC 실패인가?
1362 | → CRD·Endpoint·Service 실패인가?
1363 | → Installer 내부 Task인가?
1364 | ```
1365 | 
1366 | ### 사례 4 — KubeSphere Pod Pending
1367 | 
1368 | ```text
1369 | Node Selector
1370 | → Node Label
1371 | → Taint·Toleration
1372 | → PVC
1373 | → Resource Request
1374 | → Scheduler Event
1375 | ```
1376 | 
1377 | ### 사례 5 — Host Join 후 Cluster 상태 Error
1378 | 
1379 | ```text
1380 | Member 자체 정상
1381 | → Member Agent
1382 | → Host→Member API
1383 | → DNS·Firewall·TLS
1384 | → Join Credential
1385 | → Host Component
1386 | ```
1387 | 
1388 | ### 사례 6 — Host Join 후 Monitoring만 안 보임
1389 | 
1390 | ```text
1391 | Member external Monitoring 정상
1392 | → Cluster Label
1393 | → Prometheus Endpoint
1394 | → Host Multi-Cluster Monitoring 경로
1395 | ```
1396 | 
1397 | ### 사례 7 — 신규 Join 후 기존 Member 상태도 이상
1398 | 
1399 | 추가 변경을 중단한다. Host 공통 Component·Config가 바뀌었는지 확인하고 영향 범위를 우선 고정한다.
1400 | 
1401 | ## 35. 예상 질문
1402 | 
1403 | | 예상 질문 | 답변 핵심 | 현재 답변 가능 여부 |
1404 | |---|---|---|
1405 | | Member Monitoring을 왜 KubeSphere 전에 설치하나요? | DKS external Monitoring 선행 설계 | 미평가 |
1406 | | PVC Bound면 Monitoring Storage는 정상 아닌가요? | Pod Mount·데이터 사용 별도 | 미평가 |
1407 | | CRD가 왜 먼저 필요한가요? | API가 Custom Resource Kind를 알아야 함 | 미평가 |
1408 | | ETCD Service가 있는데 Target은 왜 Down인가요? | Service 존재와 TLS Scrape 성공은 별도 | 미평가 |
1409 | | Grafana와 KubeSphere가 같은 Prometheus URL을 쓰지 않나요? | 소비 목적과 Service가 다를 수 있음 | 미평가 |
1410 | | Host Manifest를 Member에 복사하면 안 되나요? | Role·ETCD·Domain·Monitoring·Identity가 다름 | 미평가 |
1411 | | Console이 열리면 Member 설치가 끝난 건가요? | Task·Monitoring·Storage·Role·배치 별도 | 미평가 |
1412 | | 기존 Host도 다시 설치해야 Join되나요? | 기존 Host는 완료 상태, Join 대상만 확인 | 미평가 |
1413 | | Host Console에 보이면 Join 성공 아닌가요? | Resource·Monitoring·Agent·API까지 확인 | 미평가 |
1414 | | Join Secret을 교육 자료에 적어두면 안 되나요? | 보호된 값은 승인된 관리체계로만 전달 | 미평가 |
1415 | | 9/3에 완료하지 못하면 9/4에 이어서 하면 되나요? | 9/4는 철수일, 기술 Buffer가 아님 | 미평가 |
1416 | 
1417 | ## 36. 현장 기록 양식
1418 | 
1419 | ```text
1420 | 작업일: 2026-09-03
1421 | 신규 Member Cluster/context: __________________________
1422 | 기존 Host Cluster: ___________________________________
1423 | 
1424 | Storage Gate 재확인: _________________________________
1425 | Preliminary Components: ______________________________
1426 | CRD Established: _____________________________________
1427 | Prometheus Stack: ____________________________________
1428 | Monitoring PVC·Mount: ________________________________
1429 | Monitoring Ingress: __________________________________
1430 | External ETCD Target: ________________________________
1431 | Grafana Datasource·Dashboard: _________________________
1432 | Member KubeSphere Task: ______________________________
1433 | clusterRole=member: __________________________________
1434 | Platform Workload 배치: ______________________________
1435 | Pre-Join Gate: ________________________________________
1436 | Existing Host Join: __________________________________
1437 | Host Console Status: _________________________________
1438 | Multi-Cluster 관리·관측: _____________________________
1439 | 기존 Cluster 회귀 확인: ______________________________
1440 | 
1441 | 최종 판정: PASS / PARTIAL / BLOCKED
1442 | 잔여 항목: ___________________________________________
1443 | 담당 영역·다음 조치: _________________________________
1444 | 보호된 값 정리 완료: _________________________________
1445 | 증적 위치: ___________________________________________
1446 | ```
1447 | 
1448 | ## 37. 9/3 완료 기준
1449 | 
1450 | - [ ] 9/2 Storage Gate를 다시 확인했다.
1451 | - [ ] 대상 Member Identity와 실제값을 다른 Cluster와 구분했다.
1452 | - [ ] Monitoring Namespace·Secret·PVC 선행조건이 정상이다.
1453 | - [ ] Prometheus Operator CRD가 `Established`다.
1454 | - [ ] DKS custom Monitoring Component가 정상이다.
1455 | - [ ] Monitoring PVC가 실제 Mount되고 사용된다.
1456 | - [ ] Prometheus 주요 Target과 External ETCD Target이 `UP`이다.
1457 | - [ ] Cluster·Stage External Label이 현재 Member와 일치한다.
1458 | - [ ] Grafana Datasource·Query·Dashboard가 정상이다.
1459 | - [ ] Monitoring Ingress·VIP-B·HTTP가 정상이다.
1460 | - [ ] Member KubeSphere Installer Task가 성공했다.
1461 | - [ ] Member ClusterConfiguration의 Storage·Registry·ETCD·Monitoring 값이 정확하다.
1462 | - [ ] `multicluster.clusterRole=member`다.
1463 | - [ ] KubeSphere Platform Workload가 DKS Infra 배치 정책을 따른다.
1464 | - [ ] Member 자체 Pre-Join Gate를 통과했다.
1465 | - [ ] 기존 Host를 재설치·재구성하지 않았다.
1466 | - [ ] 승인된 방식으로 기존 Host Join을 완료했다.
1467 | - [ ] Host Console에서 신규 Member Status가 정상이다.
1468 | - [ ] Host에서 Member Resource·Monitoring 관리·관측이 가능하다.
1469 | - [ ] 기존 Host·PRD·DEV Member에 회귀 영향이 없다.
1470 | - [ ] Secret·Token·JWT·kubeconfig·Private Key 원문을 노출하지 않았다.
1471 | - [ ] 8/31~9/3 기능별 인수 매트릭스를 완성했다.
1472 | - [ ] Pass·Partial·Blocked를 증거로 판정했다.
1473 | - [ ] 잔여 항목의 영향·담당자·다음 조치를 기록했다.
1474 | - [ ] 9/4 철수 전 인계·증적·접근 정리 항목을 확정했다.
1475 | 
1476 | ## 38. 9/4와 연결
1477 | 
1478 | 9/4는 기술 작업 Buffer가 아니다. 9/3 종료 시점에 기술 판정을 확정하고, 9/4에는 다음만 수행한다.
1479 | 
1480 | ```text
1481 | 현장 일정 정리
1482 | → 증적·문서·잔여 항목 인계
1483 | → 보호된 값·임시 파일·접근 정리
1484 | → 현지 담당자 확인
1485 | → 철수 준비와 이동
1486 | ```
1487 | 
1488 | 관련 문서: [[2026-09-04 현장 정리 및 철수|2026-09-04 현장 정리 및 철수]]
1489 | 
```

## Skipped Files

None.
