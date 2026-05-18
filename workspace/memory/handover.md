# 任务交接 (Handover) - 票牛项目极简版

## 🎯 当前目标
实现票牛 H5 详情页具体票源数据的稳定收割。

## 🛠️ 当前方案 (v13.8)
- **精准狙击**：使用 `.bottom-btn.direct-tag` 锁定购买按钮。
- **超级耐心**：点击后预留 **15-20 秒** 网络加载缓冲。
- **信息固化**：JSON 顶部强制补全演出日期与场馆。

## 🧪 测试重点
1. **具体页面唤起**：确认“立即购买”点击后是否真正出现了选票面板。
2. **网络抗性**：验证在慢速网络下，脚本是否能通过超长等待成功拿到数据。
3. **数据结构**：确认 `original_tiers` 是否包含具体票源列表。

## 📂 核心路径
- **脚本**：`code/tix_workflow/skills/piaoniu_full_flow.py`
- **产出**：`c:/tix_work_bench/Piaoniu_Auto_Report/`

---
*AI Assistant: Antigravity | 2026-05-07*
