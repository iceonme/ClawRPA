# 票牛（Piaoniu）全流程自动化收割系统 (v12.6) 验收文档

## 1. 任务背景
针对票牛 H5 平台的高强度风控（入场白屏、搜索拦截、交互干扰），建立一套工业级的自动化采集流水线。

## 2. 核心技术实现
- **环境重生 (Rebirth)**：强制杀掉所有 Chrome 进程，每次运行生成动态 User-Data-Dir，彻底隔离指纹。
- **潜伏进入策略**：先进入首页热身（加载 Cookie），再通过 JS 伪装跳转至搜索 URL，绕过 Referer 检查。
- **三点强穿跳转**：同步点击卡片的图片、标题和价格区域，确保 100% 进入详情页。
- **坐标物理重击**：计算底部“购买”按钮的屏幕坐标进行物理点击，解决 JS 点击被遮挡或失效的问题。
- **地毯式嗅探**：全页面扫描类似面值的节点，并自动适配“档位模式”和“直列模式”。

## 3. 验证结果
### 3.1 数据产出
- **目标场次**：广州 周传雄
- **报告路径**：[广州 周传雄_v12_6_done.json](file:///c:/tix_work_bench/Piaoniu_Auto_Report/%E5%B9%BF%E5%B7%9E%20%E5%91%A8%E4%BC%A0%E9%9B%84_v12_6_done.json)
- **数据行数**：3798 行
- **采集结构**：`场次` -> `原始面值` -> `具体票源及实时售价`

### 3.2 诊断截图
- **搜索结果**：![search_results](file:///c:/Projects/CloudPhone/workspace/01_data/debug/v12_4_search_results.png)
- **详情页状态**：![detail_page](file:///c:/Projects/CloudPhone/workspace/01_data/debug/v12_4_detail_page.png)
- **终极收割现场**：![final_diagnostic](file:///c:/Projects/CloudPhone/workspace/01_data/debug/v12_6_final_diagnostic.png)

## 4. 后续建议
- **频率控制**：建议单 IP 运行间隔不低于 5 分钟。
- **代理池**：若要进行全国规模的收割，需接入动态住宅代理池。

---
**验收人**：Antigravity (AI Coding Assistant)
**日期**：2026-05-07
