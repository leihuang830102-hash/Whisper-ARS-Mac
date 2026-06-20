# Phase 0：现成 App 验收 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 安装并配置一个成熟 macOS ASR app（本地 Whisper Large v3 Turbo），跑完验收测试，判定是否需要进 Phase 1（自研后处理管道）。

**Architecture:** 直接用现成 app 覆盖"热键→录音→本地转写→键入光标处"核心闭环；本阶段不写产品代码，只做安装、配置、权限、验收。关键判定点是 app 能否在"转写"与"键入"之间外挂后处理。

**Tech Stack:** macOS（Apple M5 / 24GB / Metal 4），候选 app SuperWhisper 或 MacWhisper，本地 Whisper Large v3 Turbo（Q8），Ollama（已装，本阶段仅探测后处理可行性）。

**Spec 参考:** `docs/superpowers/specs/2026-06-20-local-stt-design.md` §5（Phase 0 验收）。

**本仓库状态:** 非 git 仓库。Task 1 会初始化 git 以便记录配置文件变更。

---

### Task 1: 初始化项目仓库与目录结构

**Files:**
- Create: `.gitignore`
- Create: `phase0/` （存放本阶段产物：配置导出、验收记录）
- Create: `phase0/README.md`

- [ ] **Step 1: 初始化 git 仓库**

Run:
```bash
cd /Users/lei/AI_Projects/Whisper
git init
git add docs goal.md
git commit -m "chore: initial design spec and phase 0 plan"
```
Expected: 仓库初始化，首次 commit 包含 goal.md 与 docs/。

- [ ] **Step 2: 写 .gitignore**

Create `.gitignore`:
```gitignore
# macOS
.DS_Store

# 模型权重（体积大，不入库）
*.mlmodel
*.gguf
*whisper*turbo*

# 录音/转写中间产物
phase0/recordings/
phase0/raw_transcripts/

# 本地环境
.env
.env.local
```

- [ ] **Step 3: 建 phase0 目录与说明**

Create `phase0/README.md`:
```markdown
# Phase 0 产物

本目录存放"现成 app 验收"阶段的非代码产物：

- `config-export/`：从 app 导出的配置（热键、模型、模式等），用于复现与回顾。
- `acceptance.md`：验收测试记录（每项的实测值与是否达标）。
- `decision.md`：Phase 0 结论 —— 进 Phase 1 还是收工，理由。

录音与 raw 转写文本不入库（见根 .gitignore）。
```

- [ ] **Step 4: 提交**

```bash
git add .gitignore phase0/README.md
git commit -m "chore: phase 0 scaffolding (gitignore, phase0 dir)"
```

---

### Task 2: 候选 app 选型确认（SuperWhisper vs MacWhisper）

**Files:**
- Create: `phase0/app-selection.md`

**背景：** SuperWhisper 偏可配置/支持本地后处理（AI refinement），MacWhisper 偏简洁转录。本阶段关键需求是"能否外挂/内置后处理"，SuperWhisper 更可能满足。但仍需一步确认。

- [ ] **Step 1: 核对两个 app 对四项关键能力的支持**

打开两个 app 官网/文档，填入 `phase0/app-selection.md`：

```markdown
# 候选 App 选型

| 能力 | SuperWhisper | MacWhisper | 来源 |
|---|---|---|---|
| 本地 Whisper V3 Turbo | ? | ? | <链接> |
| push-to-talk + toggle 双模式 | ? | ? | <链接> |
| 键入到光标处 | ? | ? | <链接> |
| 离线运行（无云端） | ? | ? | <链接> |
| 后处理可外挂（命令/剪贴板/webhook/内置本地 LLM） | ? | ? | <链接> |

## 选定：<SuperWhisper 或 MacWhisper>
## 理由：<一句话>
```

判定规则：**第 5 行（后处理可外挂）支持者优先**。若两者都不支持外挂，仍选定转录/热键更稳的那个，并在 Task 7 标注"需进 Phase 1"。

- [ ] **Step 2: 提交选型记录**

```bash
git add phase0/app-selection.md
git commit -m "docs(phase0): app selection comparison"
```

---

### Task 3: 安装选定的 App

**Files:** 无（系统安装）

- [ ] **Step 1: 用 Homebrew 安装（首选 cask）**

Run:
```bash
brew install --cask superwhisper
# 若 Task 2 选定 MacWhisper，改为：
# brew install --cask macwhisper
```
Expected: 安装成功，`/Applications/` 下出现该 app。

若 cask 不存在，回退：从官网下载 .dmg 手动安装，并在 `phase0/app-selection.md` 追加"手动安装"备注。

- [ ] **Step 2: 首次启动并跳过云端登录**

启动 app，**不登录任何云端账号**，选 offline / local-only 模式。
Expected: app 进入主界面，无强制云端绑定。

- [ ] **Step 3: 记录版本号**

Run（以 SuperWhisper 为例）:
```bash
defaults read /Applications/Superwhisper.app/Contents/Info.plist CFBundleShortVersionString
```
把版本号追加到 `phase0/app-selection.md`。

---

### Task 4: 下载并配置本地 Whisper Large v3 Turbo 模型

**Files:**
- Modify: `phase0/config-export/model.md`

- [ ] **Step 1: 在 app 内下载 Turbo 模型**

app 设置 → Models → 选 **Whisper Large v3 Turbo**，触发下载。
Expected: 模型下载完成（本地缓存，~1.5GB 量级）。下载路径记入 `phase0/config-export/model.md`。

- [ ] **Step 2: 设为默认模型 + 中文偏好**

设置默认模型 = Turbo。若 app 支持 initial prompt / language hint，填中文提示以提升中文+英文术语识别：

`phase0/config-export/model.md`:
```markdown
# 模型配置

- 引擎/模型：Whisper Large v3 Turbo（本地）
- 默认：是
- 语言提示：zh（中文为主）
- initial prompt（若 app 支持）："以下是一段中文口语，可能包含少量英文技术术语，如 agent、prompt、token。"
- 离线：是
```

- [ ] **Step 3: 确认无云端调用**

临时断网（关 Wi-Fi），录一句短话转写。
Expected: 仍能正常转写。若失败说明模型未真正本地化，回到 Step 1 检查。

- [ ] **Step 4: 提交配置记录**

```bash
git add phase0/config-export/model.md
git commit -m "docs(phase0): local turbo model config"
```

---

### Task 5: 配置触发模式（push-to-talk + toggle）与输出

**Files:**
- Modify: `phase0/config-export/trigger.md`

- [ ] **Step 1: 配置全局热键**

在 app 设置里设一个全局热键（建议 `Option+空格` 或 `Fn`，避开与 VS Code/浏览器/终端常用快捷键冲突）。记入 `phase0/config-export/trigger.md`：

```markdown
# 触发与输出配置

- 全局热键：<实际按键>
- 模式：push-to-talk（按住说话）与 toggle（按一下开始/再按一下结束）—— 两者均启用并可切换
- 输出：键入到当前光标处
```

若 app 只支持其中一种模式，记录"仅支持 X 模式"，并在 Task 7 标注（这是 Phase 2 自研的动机之一，但不阻塞 Phase 0）。

- [ ] **Step 2: 配置输出 = 键入光标处**

确认输出目标设为"typed input / paste at cursor"，不是"复制到剪贴板手动粘贴"。

- [ ] **Step 3: 提交**

```bash
git add phase0/config-export/trigger.md
git commit -m "docs(phase0): trigger modes and output config"
```

---

### Task 6: 授予 macOS 权限

**Files:** 无（系统设置）

- [ ] **Step 1: 麦克风权限**

系统设置 → 隐私与安全性 → 麦克风 → 允许该 app。
首次录音时系统会弹窗，点允许。

- [ ] **Step 2: 辅助功能权限（全局热键 + 模拟键入必需）**

系统设置 → 隐私与安全性 → 辅助功能 → 允许该 app。
Expected: 全局热键在任意 app 聚焦时都能触发。

- [ ] **Step 3: 验证权限生效**

切到 VS Code，按热键说一句"测试权限"，松开。
Expected: 文字出现在 VS Code 光标处。若未出现，回 Step 1/2 检查开关。

---

### Task 7: 跑验收测试（§5.2 全部 5 项）

**Files:**
- Create: `phase0/acceptance.md`

- [ ] **Step 1: 准备 10 段测试语料（中文为主，含英文术语）**

在 `phase0/acceptance.md` 列 10 句话，例如：
```
1. 帮我把这个函数重构一下，抽取成一个工具方法
2. 给 agent 加一个 system prompt，限制 token 用量
3. ...
```
覆盖场景：技术对话、含英文术语、短句、长段。

- [ ] **Step 2: 测准确率（验收项①）**

对每句用 app 转写，记录 raw 输出，人工校对错字数。填表：
```markdown
| # | 原话字数 | 错字数 | 准确率 |
|---|---|---|---|
| 1 | 18 | 1 | 94% |
...
| 平均 | | | <X>% |
```
达标线（初值）：平均 ≥ 90%。

- [ ] **Step 3: 测延迟（验收项②）**

对 3 段短句，掐表测"松开热键 → 文字出现"耗时。达标线（初值）：≤ 3 秒。
记录入表。

- [ ] **Step 4: 测热键手感（验收项③）**

在 VS Code / Chrome / 终端 各按热键转写 5 次。记录是否每次都触发、有无冲突。
达标线：15 次全部触发，无快捷键冲突。

- [ ] **Step 5: 测外挂后处理可行性（验收项④ —— 关键决策项）**

查 app 设置/文档，确认能否在"转写"和"键入"之间插入一步。检查清单（任一满足即达标）：
- [ ] 支持 post-processing command / shell hook
- [ ] 支持"先输出到剪贴板/文件，由外部脚本接管"
- [ ] 内置本地 LLM refinement（可接 Ollama 端点 `http://localhost:11434`）

记录结果到 `phase0/acceptance.md` 的"外挂后处理"小节，含证据（截图路径或文档链接）。

- [ ] **Step 6: 测隐私（验收项⑤）**

断网状态下转写一句。
Expected: 正常工作。记录"断网可用 = 是"。

- [ ] **Step 7: 汇总验收结论并提交**

在 `phase0/acceptance.md` 末尾写：
```markdown
## 结论
- ① 准确率：<实测>% （达标/未达）
- ② 延迟：<实测>s （达标/未达）
- ③ 热键：<通过/失败>
- ④ 外挂后处理：<可/不可> —— 证据：<>
- ⑤ 隐私：断网可用=<是/否>
```
```bash
git add phase0/acceptance.md
git commit -m "docs(phase0): acceptance test results"
```

---

### Task 8: 决策门 —— 进 Phase 1 还是收工

**Files:**
- Create: `phase0/decision.md`

- [ ] **Step 1: 按决策规则判定**

规则（对应 spec §5.3）：
- 若 ①②③⑤ 达标 且 ④=可外挂 → **Phase 0 收工**，直接配后处理（用 app 内置本地 LLM 或外挂脚本）。
- 若 ①②③⑤ 达标 但 ④=不可外挂 → **进 Phase 1**（自研后处理管道）。
- 若 ①②③ 多项不达标 → **进 Phase 2**（完全自研）。

- [ ] **Step 2: 写决策记录**

Create `phase0/decision.md`:
```markdown
# Phase 0 决策

- 判定：<收工 / 进 Phase 1 / 进 Phase 2>
- 依据：<引用 acceptance.md 的具体数字>
- 下一步动作：<具体到要做什么>
```

- [ ] **Step 3: 提交并结束 Phase 0**

```bash
git add phase0/decision.md
git commit -m "docs(phase0): phase 0 decision gate"
```

---

## 自检（writing-plans self-review）

- **Spec 覆盖**：spec §5.1（动作：装 app、配 Turbo、配触发、输出）→ Task 3/4/5/6；§5.2（5 项验收）→ Task 7 七步全覆盖；§5.3（关键决策点：外挂后处理）→ Task 7 Step 5 + Task 8；§9（权限备忘）→ Task 6。Phase 3/4 明确非本计划范围（spec §10）。✅
- **占位符扫描**：app 选型表里的 `?` 是待填实测值（数据采集，非计划占位），合理；无 TBD/TODO/"稍后实现"。✅
- **一致性**：触发模式 push-to-talk + toggle 在 Task 5 与 spec §3 决策 2 一致；模型名 "Whisper Large v3 Turbo" 全文统一。✅
