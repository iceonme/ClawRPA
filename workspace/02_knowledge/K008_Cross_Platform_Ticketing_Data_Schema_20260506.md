# K008 跨平台票务比价数据规范 (v1.0)

## 一、 核心设计理念
为了实现摩天轮、票牛、有票等二级平台的横向对比，必须建立统一的“度量衡”。

## 二、 归一化字段标准 (Field Standards)

| 字段名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `session_id` | String | 归一化日期。格式：YYYY-MM-DD | `2026-05-16` |
| `tier_id` | String | 票面价档位（唯一Key）。数字 | `355` |
| `tier_name` | String | 平台原始档位名称 | `355票面 看台` |
| `platform` | Enum | 来源平台 | `moretickets`, `piaoniu`, `ypiao` |
| `original_price` | Number | 大麦/官方原价 | `355.0` |
| `selling_price` | Number | 当前实际卖价 | `1223.0` |
| `premium_rate` | Float | 溢价率。计算公式：(卖价-原价)/原价 | `2.44` |
| `inventory_level` | Enum | 库存饱和度 | `LOW`, `NORMAL`, `HIGH` |

## 三、 档位对齐逻辑 (Mapping Logic)
*   **数字提取**：从平台描述（如“看台355元”）中提取第一个有效的金额数字作为 `tier_id`。
*   **场次去敏**：忽略星期、天气等冗余信息，仅保留日期。

## 四、 存储位置
所有项目级的比价数据应存放在：
`c:\tix_work_bench\Event_[ProjectName]\inventory\comparison_matrix.json`
