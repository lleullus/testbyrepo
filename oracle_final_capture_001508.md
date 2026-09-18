下面给出一份可直接落地的实现计划，按“先做什么、文件怎么放、核心算法怎么设计、怎么测”展开。默认推荐 **小包结构**，同时保留一个 `trim.py` 入口，满足 `python trim.py input.txt output.txt` 的验收要求。

---

# 实现计划：系统日志 Pattern-based 相似度 Trimming CLI

## 1. 目标重述

开发一个 Python CLI 工具，对系统日志做“模式抽取 + 相似度归组 + 压缩输出”。

核心能力：

1. 自动识别变量部分
   例如：IP、UUID、MAC、timestamp、数字、域名、路径、端口、pod/container/hash 等。
2. 将模式相似度超过阈值的日志归组
   默认阈值建议 `0.85`，允许 CLI 参数调到 `0.80~0.90`。
3. 输出压缩后的日志模式及计数
4. 以单文件或小包方式实现
5. 覆盖模式提取、相似度计算、归组逻辑和 CLI 测试

---

# 2. 推荐实现形态

## 推荐：小包 + 单入口脚本

这样更利于测试和扩展，但对用户仍保持单命令使用方式。

### 文件结构

```text
project/
├─ trim.py                         # 主入口，支持 python trim.py input.txt output.txt
├─ logtrim/
│  ├─ __init__.py
│  ├─ cli.py                       # 参数解析、主流程编排
│  ├─ models.py                    # 数据结构：LogLine, LogPattern, TrimmedLog
│  ├─ patterns.py                  # 变量识别与模式抽取
│  ├─ similarity.py                # 相似度计算
│  ├─ grouping.py                  # 归组逻辑
│  ├─ io_utils.py                  # 读写文件 / stdin / stdout
│  └─ report.py                    # 输出格式与统计摘要
├─ tests/
│  ├─ test_pattern_extraction.py
│  ├─ test_similarity.py
│  ├─ test_grouping.py
│  └─ test_cli.py
├─ requirements.txt
└─ README.md
```

## 可选：单文件实现

如果你希望极简，也可以先把逻辑全部放进 `trim.py`，但测试会更难拆分。
更实际的方案是：**内部用小包，外部保留单脚本入口**。

---

# 3. 核心设计原则

## 3.1 先“标准化”，再“相似比较”

不要直接拿原始日志做模糊比对，否则变量噪声太高。流程应为：

```text
raw line
  -> tokenize / normalize
  -> variable detection
  -> pattern extraction
  -> pattern similarity
  -> grouping / counting
```

## 3.2 优先做“模式占位符替换”

例如：

原始日志：

```text
2026-04-24T10:11:12Z kubelet[1234]: Failed to pull image 10.2.3.4:5000/app:v1 for pod web-7d9f8b6d9f-abcde on node ip-10-0-1-5
```

提取后模式：

```text
<TIMESTAMP> kubelet[<NUM>]: Failed to pull image <IP>:<PORT>/<PATH> for pod <IDENT> on node <IDENT>
```

这样后续相似度会稳定很多。

## 3.3 相似度阈值不要写死

默认 `0.85`，CLI 提供：

```bash
python trim.py input.txt output.txt --threshold 0.85
```

验收里的 “80~90%” 就映射成 `0.80 ~ 0.90` 的可调范围。

## 3.4 小批量优化，不追求超大规模索引

约束里明确是几 MB 到几百 MB。
所以实现上应追求：

* 单机内存处理可接受
* 尽量减少 O(n²) 的全量比较
* 通过“候选桶”减少相似比较次数

---

# 4. 模块设计

## 4.1 `models.py`

建议用 `dataclasses`。

```python
@dataclass
class LogLine:
    raw: str
    pattern: str
    timestamp: datetime | None = None

@dataclass
class LogPattern:
    pattern: str
    count: int
    sample: str
    first_seen: datetime | None = None
    last_seen: datetime | None = None

@dataclass
class TrimmedLog:
    patterns: list[LogPattern]
    original_count: int
    trimmed_count: int
    compression_ratio: float
```

### 责任

* 明确领域模型
* 方便测试和输出序列化
* 与 `seed.yaml` 的 ontology 对齐

---

## 4.2 `patterns.py`

这是最关键的模块。

### 职责

1. 识别 timestamp
2. 识别变量 token
3. 将变量替换成占位符
4. 输出规范化 pattern

### 建议分层

#### A. 预定义正则规则

从高确定性类型开始：

* `TIMESTAMP`
* `IPV4`
* `IPV6`
* `UUID`
* `MAC`
* `HEX`
* `PORT`
* `NUMBER`
* `DOMAIN`
* `PATH`
* `EMAIL`
* `HASH`
* `POD_ID / CONTAINER_ID / K8S resource-like token`

#### B. 轻量启发式规则

用于识别不完全规则化的变量片段：

* 长数字串 -> `<NUM>`
* `abc-123-def-456` 这种混合实例名 -> `<IDENT>`
* 很长的随机字母数字串 -> `<ID>`
* 含大量数字的 token -> `<MIXED_ID>`

#### C. 标准化策略

* 保留日志模板中的稳定词
* 替换波动值
* 归一大小写可设为可选，默认不强制 lower，但建议比较时 lower
* 合并多空格

### 推荐规则顺序

顺序很重要，避免互相误伤：

1. timestamp
2. UUID
3. MAC
4. IP
5. domain
6. path
7. hash / hex
8. port
9. numeric
10. heuristic ident

### 占位符集合建议

```text
<TIMESTAMP>
<IP>
<UUID>
<MAC>
<DOMAIN>
<PATH>
<PORT>
<NUM>
<HEX>
<HASH>
<ID>
<IDENT>
```

### timestamp 解析策略

* 先用 regex 快速识别常见格式
* 再用 `dateutil.parser.parse` 尝试解析
* 解析失败不报错，返回 `None`

### 例子

```text
2026-04-24 12:00:01 node-1 kubelet: Back-off restarting failed container myapp-7f9c8d in pod web-abcde_123
```

抽取后：

```text
<TIMESTAMP> <IDENT> kubelet: Back-off restarting failed container <IDENT> in pod <IDENT>
```

---

## 4.3 `similarity.py`

### 目标

比较两个 pattern 的相似度。

### 推荐实现

优先级：

1. 如果装了 `rapidfuzz`，使用它
2. 没装时回退到标准库 `difflib.SequenceMatcher`

### 建议提供两个层级的相似度

#### A. 字符串级相似度

适合整体模板近似：

* `rapidfuzz.fuzz.ratio`
* 或 `SequenceMatcher(None, a, b).ratio()`

#### B. token 级加权相似度

更鲁棒，尤其对日志文本有意义：

* 按空格分词
* 计算 token 序列相似度
* 对占位符 token 降权，对稳定关键词升权

### 最实用方案

直接实现一个组合得分：

```text
final_score = 0.7 * normalized_string_similarity + 0.3 * token_jaccard_or_sequence_similarity
```

其中：

* `normalized_string_similarity`：整体字符相似
* `token similarity`：避免只因局部位置变化导致误判

### 额外优化：快速拒绝条件

在真正计算相似度前先做廉价过滤：

* 长度差过大 -> 拒绝
* token 数差过大 -> 拒绝
* 共享稳定词过少 -> 拒绝
* 占位符结构差异过大 -> 拒绝

这样能显著减少比较次数。

---

## 4.4 `grouping.py`

### 目标

将新日志模式归入已有组，或创建新组。

### 建议算法

#### 基本流程

对每条日志：

1. 提取 `pattern`
2. 生成 `bucket key`
3. 仅在相同 bucket 中找候选组
4. 计算相似度
5. 若最高分 >= threshold，则并入该组；否则新建组

### Bucket 设计

为了避免全量 O(n²)：

#### 可用 bucket key

选一个稳定但不过度细的 key：

```text
(
  token_count_bucket,
  first_non_placeholder_tokens,
  placeholder_signature
)
```

例如：

* `token_count_bucket = len(tokens) // 3`
* `first_non_placeholder_tokens = 前2~3个稳定词`
* `placeholder_signature = 占位符序列简写，如 T-ID-kubelet-NUM`

这样可以大幅缩小候选集合。

### Group 更新逻辑

每个 group 保存：

* `pattern`: 当前代表模式
* `sample`: 第一条原始日志
* `count`
* `first_seen`
* `last_seen`

### 是否更新代表 pattern

建议：

* 初版不频繁替换，保持第一次出现的 pattern 作为代表
* 可选增强：若新 pattern 更“泛化”或更短更稳，则更新代表 pattern

初版保持简单即可。

---

## 4.5 `io_utils.py`

### 输入

* 文件路径
* `stdin`

### 输出

* 输出文件路径
* 可选 `stdout`

### 设计建议

#### 读取接口

```python
def iter_lines(input_path: str | None) -> Iterator[str]:
    ...
```

* `input_path` 为 `-` 或 `None` 时读 stdin
* 自动剥离换行
* 跳过空行可做成参数

#### 输出接口

```python
def write_trimmed_output(result: TrimmedLog, output_path: str | None) -> None:
    ...
```

---

## 4.6 `report.py`

### 输出格式建议

兼顾人读和后处理：

```text
# summary
original_count: 12000
trimmed_count: 530
compression_ratio: 95.58%

# patterns
[1523] <TIMESTAMP> kubelet[<NUM>]: Back-off restarting failed container <IDENT> in pod <IDENT>
  sample: 2026-04-24T11:22:33Z kubelet[1234]: Back-off restarting failed container myapp in pod web-7d9f...
  first_seen: 2026-04-24T11:22:33+00:00
  last_seen: 2026-04-24T11:45:11+00:00

[987] <TIMESTAMP> Failed to connect to <IP>:<PORT>
  sample: 2026-04-24 11:23:01 Failed to connect to 10.0.0.12:6443
```

### 排序

* 按 `count desc`
* 次级按 `first_seen`

---

## 4.7 `cli.py` / `trim.py`

### CLI 参数

最少：

```bash
python trim.py input.txt output.txt
```

建议增强：

```bash
python trim.py input.txt output.txt \
  --threshold 0.85 \
  --min-stable-tokens 1 \
  --format text \
  --max-candidates 50 \
  --case-insensitive \
  --show-summary
```

### 参数定义建议

* `input`：输入文件，支持 `-` 表示 stdin
* `output`：输出文件，支持 `-` 表示 stdout
* `--threshold`：默认 0.85
* `--format`：`text` / `json`
* `--no-timestamp-parse`：禁用时间解析
* `--case-insensitive`
* `--max-candidates`：单 bucket 最多比较多少候选，避免极端退化
* `--sort-by count|first_seen`

### 退出码

* `0`：成功
* `1`：参数错误 / 输入文件不存在 / 写出失败

---

# 5. 详细任务分解

## Phase 1：骨架搭建

### 任务

* 建项目目录
* 写 `trim.py` 入口
* 建 `logtrim/` 模块
* 建测试目录

### 输出

* 可运行空 CLI
* 基础参数解析通过

---

## Phase 2：模式抽取 MVP

### 任务

* 实现常见正则
* 实现 `extract_pattern(line) -> (pattern, timestamp)`
* 加入 token 规范化

### 验收点

* 能识别 IP / UUID / MAC / 数字 / timestamp
* 同类日志抽取出相同或高度接近 pattern

### 先支持的模式

优先顺序：

1. timestamp
2. IP
3. UUID
4. MAC
5. number
6. hex/hash
7. path
8. domain
9. heuristic ident

---

## Phase 3：相似度模块

### 任务

* 实现 `compute_similarity(a, b)`
* 提供 rapidfuzz 和 difflib 双后端
* 加入快速拒绝

### 验收点

* 相似模板高分
* 明显不同模板低分
* 阈值 0.8~0.9 可合理区分

---

## Phase 4：归组逻辑

### 任务

* 实现 group bucket
* 实现 `add_line()` / `group_patterns()`
* 更新计数和时间范围

### 验收点

* 近似模式被合并
* 差异模式不误合并
* 统计字段正确

---

## Phase 5：输出与 CLI 打通

### 任务

* 实现文件输入输出
* 输出 summary + pattern list
* 完成 `python trim.py input.txt output.txt`

### 验收点

* PowerShell 可直接执行
* stdin/stdout 正常
* 输出包含 count

---

## Phase 6：测试与调优

### 任务

* 完成单元测试与 CLI 测试
* 用小规模真实样本回归
* 调整默认阈值和 bucket 策略

### 验收点

* 测试全过
* 压缩效果和逻辑合理
* 无明显性能退化

---

# 6. 关键算法建议

## 6.1 模式抽取算法

### 推荐流程

```text
1. strip line
2. detect timestamp
3. tokenize by whitespace / punctuation-aware split
4. per token apply ordered rules:
   - timestamp
   - UUID
   - MAC
   - IP
   - DOMAIN
   - PATH
   - HASH/HEX
   - PORT
   - NUM
   - heuristic IDENT
5. rebuild normalized pattern
6. collapse spaces
```

### 注意点

* 不要把所有数字都无脑替掉
  比如错误码、HTTP 状态码有时可能是模板关键部分。
  初版仍可统一成 `<NUM>`，但要留扩展点。
* 路径和 URL 要谨慎
  `/api/v1/users/123` 应尽量归一成 `<PATH>`，否则噪声很大。
* K8s 场景下资源名很关键但又变化多
  如 pod 名、node 名、container hash，很适合归成 `<IDENT>`。

---

## 6.2 相似度算法

### 建议默认规则

```text
if patterns are exactly equal:
    return 1.0

if token_count gap too large:
    return 0.0

score = 0.7 * string_ratio + 0.3 * token_ratio
```

### token_ratio 可选实现

* token 序列 SequenceMatcher
* 或 token 集合 Jaccard
* 或“稳定 token 重合率”

推荐初版：**token 序列相似度**。

---

## 6.3 归组策略

### 初版策略

“单代表模式 + 最近似匹配”

对每条新 pattern：

1. 找 bucket
2. 遍历候选组
3. 找最高相似度
4. 分数 >= threshold -> merge
5. 否则新建 group

### 复杂度控制

使用 bucket 后，实际比较次数会明显下降。
对几 MB~几百 MB 的日志量已经足够。

---

# 7. 测试策略

重点是覆盖三类风险：

1. **模式识别错**
2. **相似度阈值不稳**
3. **归组误合并或漏合并**

---

## 7.1 `tests/test_pattern_extraction.py`

### 目标

验证变量识别和模式抽取。

### 用例建议

#### timestamp

* ISO8601
* `2026-04-24 12:00:00`
* `Apr 24 12:00:00`
* 无 timestamp

#### IP

* IPv4
* IPv6
* IP:port

#### UUID / MAC

* 标准 UUID
* 标准 MAC

#### number / hex / hash

* 普通数字
* 长 hex
* 容器 hash

#### path / domain

* `/var/log/pods/...`
* `api.internal.cluster.local`

#### K8s 风格

* pod 名
* node 名
* deployment/hash 混合名

### 断言方式

* 断言 pattern 中占位符出现
* 断言稳定文本未丢失
* 断言 timestamp 成功或失败为预期

---

## 7.2 `tests/test_similarity.py`

### 目标

验证相似度分数的单调性和阈值行为。

### 用例建议

#### 高相似

```text
Failed to connect to <IP>:<PORT>
Failed to connect to <IP>:<PORT>
```

#### 中高相似

```text
Failed to connect to <IP>:<PORT>
Failed to connect to host <IP>:<PORT>
```

#### 低相似

```text
Started kubelet service
Failed to connect to <IP>:<PORT>
```

#### 阈值边界

* 同一模板 -> > 0.95
* 轻微差异 -> 0.80~0.95
* 不同模板 -> < 0.60

### 断言方式

* 断言大小规律，不必过度绑定精确分数
* 例如 `assert score_ab > score_ac`

---

## 7.3 `tests/test_grouping.py`

### 目标

验证归组逻辑和计数。

### 用例建议

#### 完全重复

3 条同 pattern -> 1 组，count=3

#### 变量不同但模式相同

3 条不同 IP / timestamp 的同类错误 -> 1 组，count=3

#### 相似但不相同

两条仅多一个稳定词，看 threshold 高低是否合并

#### 明显不同

不同类型日志 -> 分成不同组

#### 时间范围更新

first_seen / last_seen 更新正确

### 断言方式

* 组数正确
* 计数正确
* sample 保存第一条
* 时间范围正确

---

## 7.4 `tests/test_cli.py`

### 目标

验证端到端 CLI。

### 用例建议

#### 文件输入输出

* 临时输入文件
* 执行 CLI
* 检查输出文件存在且包含 summary / count

#### stdin / stdout

* 用 subprocess 喂入文本
* 检查输出内容

#### threshold 参数

* 不同 threshold 下组数变化

#### 错误处理

* 不存在的输入路径
* 非法 threshold

### 推荐实现

用 `subprocess.run()` 真实调用：

```python
subprocess.run(
    [sys.executable, "trim.py", input_path, output_path, "--threshold", "0.85"],
    capture_output=True,
    text=True,
)
```

---

# 8. 测试数据设计

建议准备 3 类测试样本。

## A. 规则型样本

专门打单点规则：

* timestamp / IP / UUID / path / MAC

## B. K8s 系统日志样本

例如：

* kubelet
* container runtime
* pod scheduling
* image pull
* readiness / liveness failure
* DNS lookup
* API server connection failure

## C. 混合噪声样本

包含：

* 不规则日志
* 只有数字变化
* 语义不同但词相近的日志

这样才能验证误归组风险。

---

# 9. 输出格式建议

## 文本格式（默认）

```text
# summary
original_count: 1000
trimmed_count: 120
compression_ratio: 88.00%

# patterns
[120] <TIMESTAMP> Failed to connect to <IP>:<PORT>
  sample: 2026-04-24 10:00:01 Failed to connect to 10.0.0.1:6443
  first_seen: 2026-04-24T10:00:01
  last_seen: 2026-04-24T10:59:59
```

## JSON 格式（可选）

便于后续程序消费：

```json
{
  "original_count": 1000,
  "trimmed_count": 120,
  "compression_ratio": 88.0,
  "patterns": [
    {
      "pattern": "<TIMESTAMP> Failed to connect to <IP>:<PORT>",
      "count": 120,
      "sample": "2026-04-24 10:00:01 Failed to connect to 10.0.0.1:6443",
      "first_seen": "2026-04-24T10:00:01",
      "last_seen": "2026-04-24T10:59:59"
    }
  ]
}
```

---

# 10. 风险点与应对

## 风险 1：变量识别不全

### 表现

同类日志没被抽成同一模式。

### 应对

* 规则按类型逐步扩充
* 保留启发式 `<IDENT>`
* 测试驱动补规则

---

## 风险 2：过度泛化导致误归组

### 表现

不同问题被压成一组。

### 应对

* 保留稳定词
* 相似度加入 token 级约束
* bucket 先过滤
* 默认 threshold 设为 0.85 而不是 0.80

---

## 风险 3：性能退化

### 表现

日志量上来后比较过多。

### 应对

* 先按 bucket 分桶
* 加快速拒绝
* 限制每桶最大候选数
* 按 pattern exact match 优先命中

---

## 风险 4：timestamp 解析误判

### 应对

* “解析失败不影响模式抽取”
* 时间字段仅作为附加信息，不阻断流程

---

# 11. 里程碑建议

## M1：最小可用版本

* 读取文件
* 抽取 pattern
* exact + basic similarity grouping
* 输出 count

## M2：增强识别

* timestamp / IP / UUID / MAC / path / domain / hash
* bucket 优化
* JSON 输出

## M3：稳态版本

* CLI 完整参数
* 全测试覆盖
* README 与样例数据
* 阈值调优

---

# 12. 验收映射

根据你给出的 acceptance criteria，可这样对照：

## 1) 输入文件(path 或 stdin)读取

* `io_utils.iter_lines()`
* CLI 支持 `-` 代表 stdin

## 2) 自动检测变量部分

* `patterns.py`
* 正则 + 启发式替换

## 3) 80~90% 阈值比较

* `similarity.py`
* `--threshold 0.80~0.90`

## 4) 相似日志归组并计数

* `grouping.py`
* `LogPattern.count += 1`

## 5) 输出 trimming 结果

* `report.py`
* 文本/JSON 输出

## 6) PowerShell 可运行

* 保留根目录 `trim.py`
* 命令：

  ```powershell
  python trim.py input.txt output.txt
  ```

---

# 13. 实施顺序建议

最合理的开发顺序：

1. `models.py`
2. `patterns.py` 的基础规则
3. `similarity.py`
4. `grouping.py`
5. `io_utils.py` + `report.py`
6. `cli.py` + `trim.py`
7. 单元测试
8. 阈值和 bucket 调优

---

# 14. 建议的初版默认参数

```text
threshold = 0.85
format = text
case_insensitive = True
max_candidates_per_bucket = 50
sort_by = count
```

这组参数通常更稳：

* `0.85` 不容易过度合并
* `case_insensitive=True` 减少日志源差异
* `max_candidates_per_bucket=50` 防止极端桶膨胀

---

# 15. 一个务实的开发完成定义

当满足下面这些，就可以认为第一版完成：

* `python trim.py input.txt output.txt` 可运行
* 能正确读取文件或 stdin
* 能识别至少：timestamp、IP、UUID、MAC、数字、路径、域名
* 默认阈值 0.85 下，重复日志能明显压缩
* 输出包含 pattern、count、sample、first_seen、last_seen
* `tests/test_pattern_extraction.py`
* `tests/test_similarity.py`
* `tests/test_grouping.py`
* `tests/test_cli.py`
  全部通过

---

如果你愿意，我下一步可以直接把这个计划进一步细化成“逐文件实现说明”，包括每个文件应有哪些函数、函数签名和测试样例。
