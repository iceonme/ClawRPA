# 项目看板

## 🚀 正在进行
- [/] `weibo-rpa` 已完成第一轮收口重构（平台优先，当前先做 `lead`）
- [/] 微博 `lead` 工程化：统一入口、脚本分层、文档收口
- [/] 为后续 `chat` 子域准备状态层 / 去重 / 增量刷新基础

## 📅 待办事项
- [ ] 增加最小 `state store`（优先 SQLite）
- [ ] 落两张基础表：`lead_candidates` / `task_runs`
- [ ] 做 lead 去重 key 与增量刷新策略
- [ ] 把 `weibo_collect_test_leads.py` 往正式 pipeline 靠（并入 `run_lead_task.py` 或抽到 `src/` workflow）
- [ ] 规划 `weibo-rpa/chat` 的 task schema 与状态流转
- [ ] 如需增强，再做评论层抽取作为 `lead v2`

## ✅ 已完成
- [x] 仓库物理目录已改名为：`C:\Projects\CloudPhone\code\browser\weibo-rpa`
- [x] 已统一工程口径为：顶层 `weibo-rpa`，当前正式能力 `lead`
- [x] 已更新 `README.md` / `SKILL.md` / `pyproject.toml` / `references` 关键文档
- [x] 已新增统一入口：`scripts/run_lead_task.py` / `scripts/run_weibo_probe.py`
- [x] 已新增示例输入：`examples/lead/weibo.event.json`
- [x] 已整理 `scripts/` 为正式入口 / probe / archive 三层
- [x] 已验证新路径下主入口可正常运行
- [x] 已完成 `时代少年团 广州` 100 条 lead 测试
- [x] 已完成 `蔡依林 苏州` 20 条 lead 测试
- [x] 已确认当前高产模式主要是搜索结果页正文中的“没抢到”等强需求表达
