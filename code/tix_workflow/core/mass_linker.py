import asyncio
import subprocess
import os

projects = [
    "温州 周杰伦",
    "广州 周传雄",
    "北京 五月天",
    "深圳 凤凰传奇"
]

async def run_batch_linking():
    print("=== 开始批量项目 ID 探测 (票牛) ===")
    results = {}
    
    for proj in projects:
        print(f"\n[Batch] 正在分析项目: {proj}")
        # 调用之前写好的参数化脚本
        cmd = ["python", "code/tix_workflow/core/get_piaoniu_id.py", proj]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        output = stdout.decode('gbk', errors='ignore')
        print(output)
        
        # 提取 ID
        import re
        match = re.search(r"平台 ID: (\d+)", output)
        if match:
            results[proj] = match.group(1)
            
    print("\n=== 探测任务完成汇总 ===")
    for k, v in results.items():
        print(f"项目: {k} | 票牛 ID: {v}")

if __name__ == "__main__":
    asyncio.run(run_batch_linking())
