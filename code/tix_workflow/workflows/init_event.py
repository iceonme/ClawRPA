import os
import json
import datetime
import argparse
import re
import requests
from typing import Dict, Any

# 导入分子技能
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
skills_path = os.path.join(os.path.dirname(current_dir), "skills")
core_path = os.path.join(os.path.dirname(current_dir), "core")
if skills_path not in sys.path:
    sys.path.append(skills_path)
if core_path not in sys.path:
    sys.path.append(core_path)

from event_damai_info import fetch_damai_event_info
from prep_browser import prepare_browser_environment

def download_image(url: str, save_path: str):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"[Init] 下载图片失败 {url}: {e}")
    return False

def init_event_project(keyword: str, base_dir: str = None):
    """
    初始化一个票务项目：抓取信息、创建文件夹、下载物料、写入基础文件。
    """
    if base_dir is None:
        if sys.platform.startswith("win"):
            base_dir = "c:\\tix_work_bench"
        else:
            base_dir = os.path.expanduser("~/tix_work_bench")
    # 0. 环境准备与人工引导
    if not prepare_browser_environment():
        print("[Init] 浏览器准备失败。")
        return

    # 1. 抓取信息
    info = fetch_damai_event_info(keyword)
    if not info:
        print(f"[Init] 无法获取 {keyword} 的信息，终止初始化。")
        return

    # 2. 准备文件夹名称 (固化规则: Event_城市_艺人_日期)
    location = "未知"
    if info['venue']:
        # 同时支持半角 | 和全角 ｜
        venue_parts = re.split(r'[|｜]', info['venue'])
        location = venue_parts[0].strip()[:2]
    
    artist = keyword.replace("演唱会", "").replace("2026", "").strip()
    
    # 精准提取日期 (支持 2026.05.08 或 20260508 等格式)
    event_date = "00000000"
    date_match = re.search(r"(\d{4})[./](\d{2})[./](\d{2})", info['time'])
    if date_match:
        event_date = "".join(date_match.groups())

    folder_name = f"Event_{location}_{artist}_{event_date}"
    target_path = os.path.join(base_dir, folder_name)

    # 3. 创建目录结构
    sub_dirs = ["info", "inventory", "lead", "channel", "crm"]
    os.makedirs(target_path, exist_ok=True)
    for d in sub_dirs:
        os.makedirs(os.path.join(target_path, d), exist_ok=True)

    # 4. 下载物料 (图片)
    print("[Init] 正在下载项目物料...")
    if info.get("poster_url"):
        download_image(info["poster_url"], os.path.join(target_path, "info", "poster.jpg"))
    
    if info.get("detail_images"):
        # 下载详情图，上限提高到 20 张
        for i, img_url in enumerate(info["detail_images"][:20]):
            download_image(img_url, os.path.join(target_path, "info", f"detail_{i}.jpg"))

    # 5. 写入原始文案 (大麦原汁原味)
    with open(os.path.join(target_path, "info", "damai_description.md"), "w", encoding="utf-8") as f:
        f.write(f"# 大麦原始介绍: {info['title']}\n\n")
        f.write(info.get("artist_intro", "暂无详情"))

    # 6. 写入 info.md (由 Agent 深度汇总的版本)
    artist_intro = info.get("artist_intro", "暂无简介")
    venue_intro = info.get("venue_intro", "暂无简介")

    info_md_content = f"""# 项目基本信息: {info['title']}

## 演出概览
- **艺人**: {artist}
- **时间**: {info['time']}
- **场馆**: {info['venue']}
- **票价区间**: {info['price_range']}
- **大麦链接**: [{info['url']}]({info['url']})

## 艺人/项目简介
{artist_intro}

## 场馆简介
{venue_intro}

## 项目状态
- **初始化日期**: {datetime.datetime.now().strftime("%Y-%m-%d")}
- **状态**: 筹备中
"""
    with open(os.path.join(target_path, "info.md"), "w", encoding="utf-8") as f:
        f.write(info_md_content)

    # 6. 写入 status.json
    timestamp = int(datetime.datetime.now().timestamp())
    status_data = {
        "event_id": timestamp,
        "keyword": keyword,
        "status": "initialized",
        "last_update": datetime.datetime.now().isoformat(),
        "metrics": {
            "inventory_count": 0,
            "lead_count": 0,
            "crm_count": 0
        }
    }
    with open(os.path.join(target_path, "status.json"), "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=4)

    print(f"\n[Init] 项目初始化成功！")
    print(f"[Init] 文件夹: {target_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化票务项目")
    parser.add_argument("--keyword", type=str, required=True, help="搜索关键词")
    args = parser.parse_args()

    init_event_project(args.keyword)
