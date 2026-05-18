import json
import os
import re

def extract_price(text):
    """从文本中提取纯数字价格"""
    if not text: return None
    # 移除千分位逗号，提取第一个连续数字
    match = re.search(r"(\d+)", text.replace(",", ""))
    return int(match.group(1)) if match else None

def extract_tier(text_list):
    """从一组文本中寻找标准票面档位 (355, 655, 855, 955, 1255, 1555)"""
    standard_tiers = ["355", "655", "855", "955", "1255", "1555"]
    combined_text = " ".join([str(t) for t in text_list if t])
    for st in standard_tiers:
        if st in combined_text:
            return st
    # 如果没找到标准档位，尝试提取第一个出现的 3 位及以上数字
    match = re.search(r"(\d{3,})", combined_text)
    return match.group(1) if match else "未知"

def aggregate_data_smart():
    project_path = "c:/tix_work_bench/Event_北京五月天_20260508/inventory"
    
    # 1. 加载摩天轮数据
    mtl_path = os.path.join(project_path, "moretickets_snapshot_20260506.json")
    with open(mtl_path, "r", encoding="utf-8") as f:
        mtl_raw = json.load(f)
    
    # 2. 加载票牛数据
    pn_path = os.path.join(project_path, "piaoniu_matrix_final_20260506.json")
    with open(pn_path, "r", encoding="utf-8") as f:
        pn_raw = json.load(f)
        
    matrix = {}

    # 处理摩天轮
    for item in mtl_raw:
        tid = extract_tier([item['tier']])
        price = extract_price(str(item['secondary_price']))
        if tid and price:
            if tid not in matrix: matrix[tid] = {"tier": tid, "platforms": {}}
            matrix[tid]["platforms"]["moretickets"] = price

    # 处理票牛 (启发式校正)
    for item in pn_raw:
        # 票牛数据可能错位，我们将 tier 和 price 字段合并起来搜
        tid = extract_tier([item['tier'], item['price']])
        price = None
        
        # 如果是 ticket_detail，price 字段通常就是数字
        if item['type'] == 'ticket_detail':
            price = extract_price(item['price'])
        else:
            # 如果是 summary，由于发生了错位，我们需要在所有文本里找那个“看起来像卖价”的大数字
            # 但 summary 里的价格通常是“起步价”，我们这里优先记录 detail 里的真实报价
            continue 

        if tid != "未知" and price:
            if tid not in matrix: matrix[tid] = {"tier": tid, "platforms": {}}
            # 记录该档位的最低价
            current = matrix[tid]["platforms"].get("piaoniu", 999999)
            if price < current:
                matrix[tid]["platforms"]["piaoniu"] = price

    # 生成最终报表
    report = []
    for tid, data in matrix.items():
        p_mtl = data["platforms"].get("moretickets", "-")
        p_pn = data["platforms"].get("piaoniu", "-")
        
        # 比价逻辑
        valid_prices = [p for p in [p_mtl, p_pn] if isinstance(p, int)]
        best = min(valid_prices) if valid_prices else "-"
        source = "摩天轮" if best == p_mtl else "票牛" if best == p_pn else "-"
        
        report.append({
            "tier": tid,
            "moretickets": p_mtl,
            "piaoniu": p_pn,
            "best": best,
            "source": source
        })

    # 排序并输出
    report.sort(key=lambda x: int(x['tier']) if x['tier'].isdigit() else 0)
    
    print("\n### 🚀 五月天北京鸟巢站 - 跨平台横向比价 (2026-05-06)")
    print("| 票面价 | 摩天轮(卖价) | 票牛(卖价) | 最优选 | 推荐平台 |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    for r in report:
        print(f"| {r['tier']} | {r['moretickets']} | {r['piaoniu']} | **{r['best']}** | {r['source']} |")

    # 保存
    with open(os.path.join(project_path, "final_comparison_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    aggregate_data_smart()
