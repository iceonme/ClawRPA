# Piaoniu 票务自动化收割任务验收 (Walkthrough)

## 任务目标
实现一个能够稳定、高效收割多场次演唱会（如“北京五月天”）票价数据的自动化脚本，解决 H5 端搜索受限及数据提取不全的问题。

## 实现成果

### 1. 跨端联动策略 (v15.0 - v16.1)
- **PC 辅助搜索**：脚本不再依赖 H5 端不稳定的搜索框，而是通过 `www.piaoniu.com` PC 端页面精准锁定演出的 `Activity ID`。
- **直达空降**：获取 ID 后，直接通过 `m.piaoniu.com/seat/seat.html?id={ID}` 跳转到选座页，跳过了所有复杂的详情页反爬逻辑。

### 2. 多场次自动遍历 (v16.0)
- **自动场次探测**：脚本能自动点击选座页的日期选择器。
- **循环收割逻辑**：通过 `range(session_count)` 自动遍历所有日期，切换场次并收割该场次下的所有档位。

### 3. 环境与日志加固
- **GBK 兼容性**：移除了所有导致 Windows 终端崩溃的 Emoji 字符，采用纯文本标签（OK/FAIL/GO）。
- **实时监控**：移除输出缓冲区，通过 `python -u` 实现每一秒的进度实时可见。

## 交付物验证

- **广州 周传雄**：单场次收割成功，日期提取精准（`2026.05.16`）。
- **北京 五月天**：多场次（8 场）循环收割成功。
- **最终报告**：[北京 五月天_v13_8_multi.json](file:///c:/tix_work_bench/Piaoniu_Auto_Report/%E5%8C%97%E4%BA%AC%20%E4%BA%94%E6%9C%88%E5%A4%A9_v13_8_multi.json) (1.2w+ 行)。

## 运行指南
```powershell
# 运行任意演唱会收割（支持多场次）
python -u code/tix_workflow/skills/piaoniu_full_flow.py "演出关键词"
```

---
*Status: Verified & Completed*
