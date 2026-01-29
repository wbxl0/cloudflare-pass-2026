import json
import os
import time
import subprocess
from datetime import datetime, timedelta

# 配置文件必须放在持久化挂载目录
CONFIG_FILE = "/app/output/tasks_config.json"

def load_tasks():
    if not os.path.exists(CONFIG_FILE):
        print(f"[*] 配置文件 {CONFIG_FILE} 不存在，跳过调度")
        return []
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tasks(tasks):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def run_scheduler():
    tasks = load_tasks()
    now = datetime.now()
    updated = False

    for task in tasks:
        # 检查是否启用
        if not task.get('active', True):
            continue

        # 获取上次运行时间
        last_run_str = task.get('last_run')
        freq_days = task.get('freq', 3) # 默认3天续期一次
        
        should_run = False
        if not last_run_str:
            should_run = True # 从未运行过，立即运行
        else:
            last_run_time = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
            # 如果当前时间 超过了 (上次运行时间 + 周期)
            if now >= (last_run_time + timedelta(days=freq_days)):
                should_run = True

        if should_run:
            print(f"[*] 正在自动执行任务: {task['name']}")
            
            # 准备临时环境变量投喂给业务脚本
            env = os.environ.copy()
            env["EMAIL"] = task['email']
            env["PASSWORD"] = task['password']
            
            # 调用你原封不动的业务脚本
            try:
                # 使用 xvfb-run 确保有显示环境
                subprocess.run(["xvfb-run", "--server-args=-screen 0 1920x1080x24", "python", task['script']], env=env, check=True)
                
                # 更新运行时间
                task['last_run'] = now.strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                print(f"[+] 任务 {task['name']} 自动续期成功")
            except Exception as e:
                print(f"[!] 任务 {task['name']} 执行失败: {e}")

    if updated:
        save_tasks(tasks)

if __name__ == "__main__":
    run_scheduler()
