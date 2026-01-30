import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

# 配置文件路径，必须与 app.py 保持一致
CONFIG_FILE = "/app/output/tasks_config.json"

def run_scheduler():
    if not os.path.exists(CONFIG_FILE):
        print("[*] 尚未配置任何任务，调度器进入待命状态。")
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except Exception as e:
        print(f"[!] 读取配置文件失败: {e}")
        return

    # --- 核心锁定：强制使用北京时间 (UTC+8) ---
    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz)
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
            try:
                # 增加了日期解析保护：如果碰到 katassv 这种乱码，会进入 except
                last_run_time = datetime.strptime(str(last_run_str), "%Y-%m-%d %H:%M:%S").replace(tzinfo=bj_tz)
                if now >= (last_run_time + timedelta(days=freq)):
                    should_run = True
            except (ValueError, TypeError):
                # 关键修复：如果 last_run 是乱码，强制判定为需要运行，从而修复掉乱码数据
                print(f"[!] 检测到无效的时间记录 '{last_run_str}'，正在强制触发以修复数据...")
                should_run = True

        if should_run:
            # 3. 提取我们在 UI 上选好的 API 模式
            selected_mode = task.get('mode', '单浏览器模式 (对应脚本: simple_bypass.py)')
            print(f"[*] [周期任务启动] 项目: {task['name']} | 挂载 API: {selected_mode}")
            
            # 4. 环境变量注入
            env = os.environ.copy()
            env["EMAIL"] = task['email']
            env["PASSWORD"] = task['password']
            env["BYPASS_MODE"] = selected_mode 
            env["PYTHONUNBUFFERED"] = "1"
            
            try:
                # 5. 统一使用 xvfb 环境执行
                # 注意：这里使用 task.get('script', 'katabump_renew.py') 增加兼容性
                script_name = task.get('script', 'katabump_renew.py')
                subprocess.run([
                    "xvfb-run", "--server-args=-screen 0 1920x1080x24", 
                    "python", script_name
                ], env=env, check=True)
                
                # 执行成功后更新时间：确保写入的是标准北京时间字符串
                task['last_run'] = now.strftime("%Y-%m-%d %H:%M:%S")
                updated = True
                print(f"[+] {task['name']} 自动同步成功。")
            except Exception as e:
                print(f"[!] {task['name']} 自动执行失败: {e}")

    # 6. 如果有运行记录更新，写回 JSON 文件
    if updated:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            print("[*] 任务配置已同步更新。")
        except Exception as e:
            print(f"[!] 写入配置文件失败: {e}")

if __name__ == "__main__":
    run_scheduler()
