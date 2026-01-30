import json
import os
import subprocess
from datetime import datetime, timedelta

# 配置文件路径，必须与 app.py 保持一致
CONFIG_FILE = "/app/output/tasks_config.json"

def run_scheduler():
    if not os.path.exists(CONFIG_FILE):
        print("[*] 尚未配置任何任务，调度器进入待命状态。")
        return

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    now = datetime.now()
    updated = False

    for task in tasks:
        # 1. 检查任务是否激活
        if not task.get('active', True): 
            continue
        
        last_run_str = task.get('last_run')
        freq = task.get('freq', 3)
        
        # 2. 自动化执行逻辑判断
        should_run = False
        if not last_run_str or last_run_str == "从未运行":
            should_run = True
        else:
            last_run_time = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
            if now >= (last_run_time + timedelta(days=freq)):
                should_run = True

        if should_run:
            # 3. 提取我们在 UI 上选好的 API 模式
            selected_mode = task.get('mode', '单浏览器模式 (对应脚本: simple_bypass.py)')
            print(f"[*] [周期任务启动] 项目: {task['name']} | 挂载 API: {selected_mode}")
            
            # 4. 环境变量注入：这是 katabump_renew.py 调用对应 API 的关键
            env = os.environ.copy()
            env["EMAIL"] = task['email']
            env["PASSWORD"] = task['password']
            env["BYPASS_MODE"] = selected_mode # 核心：将 UI 选择的 API 模式传给主脚本
            env["PYTHONUNBUFFERED"] = "1"
            
            try:
                # 5. 统一使用 xvfb 环境执行，确保 Chrome 和 API 物理点击能正常运行
                subprocess.run([
                    "xvfb-run", "--server-args=-screen 0 1920x1080x24", 
                    "python", task['script']
                ], env=env, check=True)
                
                # 执行成功后更新时间
                task['last_run'] = now.strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                print(f"[+] {task['name']} 自动同步成功。")
            except Exception as e:
                print(f"[!] {task['name']} 自动执行失败: {e}")

    # 6. 如果有运行记录更新，写回 JSON 文件
    if updated:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_scheduler()
