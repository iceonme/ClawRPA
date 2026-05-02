# History - 2026-04-19 - lead-discovery skill 初始化

## 本次目标
围绕“找潜在客户”这一类任务，先在 `C:\Projects\CloudPhone\code\browser` 下搭建一个标准 skill 目录，名称为 `lead-discovery`，并用中文完成第一版说明文档与目录骨架。

## 本次已完成

### 1. 建立了 skill 目录
已创建：

`C:\Projects\CloudPhone\code\browser\lead-discovery`

并初始化了 git 仓库。

### 2. 建立了第一版目录骨架
当前目录包括：

- `SKILL.md`
- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `references/`
- `scripts/`
- `src/core/`
- `src/flows/`
- `src/schemas/`
- `src/probes/`
- `examples/`
- `assets/`
- `runs/`

### 3. 明确了 skill 边界
`lead-discovery` 只负责：
- 围绕某个演出搜索相关帖子
- 遍历帖子与评论
- 识别潜在购票意图
- 输出结构化线索结果

明确不负责：
- 热度分析
- 主动私信 / 外联
- 自动盯票

其中“热度分析”已确定建议拆成另一个独立 skill，例如后续可命名为 `heat-analysis`。

### 4. 明确了目录分层思路
最终采用的是较轻量的 skill 结构，而不是重型 adapter 架构：

- `src/core/`：Playwright / 浏览器原子能力、human-like actions、等待策略、产物保存、配置等
- `src/flows/`：微博 / 小红书搜索、评论提取、线索判断、线索汇总
- `src/schemas/`：输入输出结构定义
- `src/probes/`：站点探针

结论：`core` 这一层仍然保留，而且是必要的。

### 5. 依赖说明已补齐
虽然本机已经有 Playwright，但已经明确：

> 本机已安装，不代表 skill 可以省略依赖说明。

因此已新增：
- `references/dependencies.md`
- `requirements.txt`

当前最小依赖表达：
- Python 3.10+
- Playwright

并在 `SKILL.md`、`README.md` 中都补了依赖说明入口。

### 6. 重新核对了 OpenClaw 官方后台进程文档，并修正了 skill 的理想设计
重点重新确认了官方文档：
- Background Exec and Process Tool
- `exec + process` 后台任务模型

最终确认：

> skill 不应按“长期裸 stdin/stdout 聊天协议”设计，
> 而应按 OpenClaw 的 `exec + process` 后台任务模型设计。

关键结论：
- 脚本可以是长任务，但默认不是持续聊天式进程
- 长任务由 OpenClaw 的后台 session 管理
- 真实产物应该落盘到 `runs/`
- stdout 只输出少量结构化状态 / 产物索引 / 最终结果
- stderr 用于调试日志和详细报错
- 大内容（DOM、评论原文等）不直接打到 stdout

### 7. 新增了 I/O 协议与架构说明
已新增：
- `references/io-protocol.md`
- `references/architecture.md`

其中明确：

#### stdout 只允许输出三类消息
- `status`
- `artifact`
- `result`

#### stderr 用于
- 调试日志
- 运行细节
- 重试信息
- 错误堆栈

#### 大内容处理方式
- 写入 `runs/<task-id>/<platform>/...`
- stdout 只提供摘要、计数、路径

### 8. 第一版中文文档已完成
已写出的中文文档包括：
- `SKILL.md`
- `README.md`
- `references/task-definition.md`
- `references/workflow.md`
- `references/output-schema.md`
- `references/review-rules.md`
- `references/human-takeover.md`
- `references/site-notes-weibo.md`
- `references/site-notes-xiaohongshu.md`
- `references/dependencies.md`
- `references/io-protocol.md`
- `references/architecture.md`

### 9. 代码占位文件已建立
已建立第一批占位代码文件：

#### `scripts/`
- `run_task.py`
- `run_probe.py`

#### `src/core/`
- `browser.py`
- `human_actions.py`
- `waits.py`
- `artifacts.py`
- `config.py`

#### `src/flows/`
- `weibo_search.py`
- `weibo_comments.py`
- `xhs_search.py`
- `xhs_comments.py`
- `lead_judgement.py`
- `lead_collection.py`

#### `src/schemas/`
- `lead.py`
- `task_input.py`
- `task_output.py`

#### `src/probes/`
- `weibo_probe.py`
- `xhs_probe.py`

## 当前共识

### 关于 skill 拆分
- `lead-discovery`：单独一个 skill，负责找潜在客户
- `heat-analysis`：建议独立 skill，后续再建

### 关于 agent / subagent
当前共识是：
- 顶层用主 agent 接任务
- 需要时起 subagent
- 同一份 `lead-discovery` skill 可以被不同 subagent 复用
- 微博 / 小红书通过不同参数运行
- 不同 subagent 的结构化输出应写到共享 workspace 下不同的 `runs/` 子目录中

### 关于输出目录
推荐模式：
- `runs/<task-id>/weibo/...`
- `runs/<task-id>/xiaohongshu/...`
- 后续可再由主 agent 合并为 merged 结果

## 当前未完成
还没有进入真正实现阶段，目前仍处于：
- skill 骨架已搭好
- 文档原则已定好
- 代码文件仍以占位为主

## 下一步最建议做的事
按优先级建议：

1. 实现 `src/core/io_protocol.py`
   - `emit_status()`
   - `emit_artifact()`
   - `emit_result()`
   - `log_debug()`

2. 完成 schema
   - `src/schemas/lead.py`
   - `src/schemas/task_input.py`
   - `src/schemas/task_output.py`

3. 先做 probe，而不是直接做完整 lead-discovery
   - `src/probes/weibo_probe.py`
   - `src/probes/xhs_probe.py`
   - `scripts/run_probe.py`

目标是先确认：
- 搜索页能否打开
- 帖子能否进入
- 评论能否读取/展开
- 运行产物如何落盘
- stdout/stderr 协议是否顺手

## 一句话 handoff
当前 `lead-discovery` skill 的方向已经确定：

> 用标准 skill 目录 + 中文说明文档 + 轻量 core/flows/schemas/probes 结构，
> 按 OpenClaw 官方 `exec + process` 后台任务模型设计，
> 通过文件落盘承载大内容，通过少量 JSON stdout 输出状态/产物索引/结果。

下一步不要直接上完整业务，先把 schema、I/O helper 和微博/小红书 probe 打通。
