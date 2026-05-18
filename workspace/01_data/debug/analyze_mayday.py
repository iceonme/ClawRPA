import json

path = r"c:/tix_work_bench/Piaoniu_Auto_Report/北京 五月天_v13_8_multi.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"演出项目: {data['event']}")
print(f"场馆: {data['venue']}")
print("-" * 30)

all_sessions = data["dates"]
for s in all_sessions:
    date = s["date"]
    tiers = s["original_tiers"]
    
    prices = []
    total_listings = 0
    for t in tiers:
        for l in t["listings"]:
            prices.append(l["current_price"])
            total_listings += 1
    
    if prices:
        min_p = min(prices)
        avg_p = sum(prices) / len(prices)
        max_p = max(prices)
        print(f"场次: {date}")
        print(f"  - 挂票总数: {total_listings}")
        print(f"  - 最低起售价: {min_p} 元")
        print(f"  - 平均挂票价: {avg_p:.2f} 元")
        print(f"  - 最高溢价标价: {max_p} 元")
    else:
        print(f"场次: {date} (无数据)")
