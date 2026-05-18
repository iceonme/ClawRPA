import json
import re

def parse_wechat_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 结果容器：date -> tier -> list of prices
    results = {}
    
    # 模拟简单的解析逻辑
    # 找到 8号, 9号... 这种标志
    sessions = re.split(r'(\d+)号', content)
    
    current_day = None
    for i in range(1, len(sessions), 2):
        day_num = sessions[i]
        day_content = sessions[i+1]
        date_key = f"2026.05.{day_num.zfill(2)}"
        if date_key not in results: results[date_key] = {}
        
        # 提取价格行，例如 "855... 800"
        lines = day_content.split('\n')
        for line in lines:
            # 匹配 档位 + 价格 (如 855 ... 800)
            price_match = re.search(r'(\d{3,4}).*?(\d{3,5})(?:x\d+)?$', line.strip())
            if price_match:
                tier = price_match.group(1)
                price = int(price_match.group(2))
                if tier not in results[date_key]:
                    results[date_key][tier] = []
                results[date_key][tier].append(price)

    # 转换为最终格式
    final_json = []
    for date, tiers in results.items():
        session_entry = {"date": date, "tiers": []}
        for tier, prices in tiers.items():
            if prices:
                session_entry["tiers"].append({
                    "tier": tier,
                    "min_price": min(prices),
                    "all_prices": prices
                })
        final_json.append(session_entry)
    
    return final_json

if __name__ == "__main__":
    data = parse_wechat_md("c:/Projects/CloudPhone/workspace/tmp/五月天微信.md")
    with open("c:/Projects/CloudPhone/workspace/01_data/wechat_mayday_full.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("WeChat Data Parsed and Saved.")
