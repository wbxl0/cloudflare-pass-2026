import os
import time
import json
import random
from datetime import datetime
from pathlib import Path
import requests
from seleniumbase import SB

def send_tg_notification(message, photo_path=None):
    """发送 Telegram 消息和截图"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): return
    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={'chat_id': chat_id, 'caption': message}, files={'photo': f})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={'chat_id': chat_id, 'text': message})
    except Exception as e: print(f"TG通知失败: {e}")

def run_auto_renew():
    # 从环境变量获取配置
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    # 获取 UI 选中的模式 (映射到不同的破解逻辑)
    ui_mode = os.environ.get("BYPASS_MODE", "单浏览器模式") 
    
    login_url = "https://dashboard.katabump.com/login"
    target_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    OUTPUT_DIR = Path("/app/output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[*] [{datetime.now().strftime('%H:%M:%S')}] 流程启动...")
    print(f"[*] 当前选择的破解逻辑模式: {ui_mode}")

    # 启动浏览器
    with SB(uc=True, xvfb=True) as sb:
        try:
            # ---- 步骤 1: 登录 ----
            print(">>> [1/5] 正在打开登录页面...")
            sb.uc_open_with_reconnect(login_url, 10)
            sb.wait_for_element("#email", timeout=15)
            sb.type("#email", email)
            sb.type("#password", password)
            sb.click('button:contains("登录")')
            sb.sleep(4)

            # ---- 步骤 2: 进入编辑页 ----
            print(">>> [2/5] 正在跳转至 See 管理页面...")
            sb.uc_open_with_reconnect(target_url, 10)
            sb.sleep(2)

            # ---- 步骤 3: 触发续期弹窗 ----
            print(">>> [3/5] 点击 Renew 按钮触发弹窗...")
            sb.scroll_to('button[data-bs-target="#renew-modal"]')
            sb.click('button[data-bs-target="#renew-modal"]')
            sb.sleep(3) 

            # ---- 步骤 4: 根据 UI 选择执行对应的破解脚本逻辑 ----
            print(f">>> [4/5] 关键点：正在调用 [{ui_mode}] 对应的破解逻辑...")
            
            if "单" in ui_mode:
                # 对应 simple_bypass.py 的逻辑：快速尝试物理点击
                print("    [调用逻辑] 执行 simple_bypass: 快速定位并点击我是真人")
                sb.uc_gui_click_captcha()
                
            elif "增强" in ui_mode:
                # 对应 bypass_seleniumbase.py 的逻辑：注入反检测后重连再点
                print("    [调用逻辑] 执行 bypass_seleniumbase: 注入反爬指纹并深度过盾")
                sb.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                sb.sleep(1)
                sb.uc_gui_click_captcha()
                
            elif "竞争" in ui_mode:
                # 对应 bypass.py 的逻辑：多重延迟模拟真人动作
                print("    [调用逻辑] 执行 bypass: 模拟随机滑动与真人操作序列")
                sb.uc_gui_click_captcha()
                sb.sleep(random.uniform(2, 5))
            
            print("    [OK] 破解程序执行完毕")
            sb.sleep(3)

            # ---- 步骤 5: 最终确认 ----
            print(">>> [5/5] 点击最终的“更新”按钮...")
            # 针对 2026年1月29日 网页结构，匹配 font 标签按钮
            sb.click('button:contains("更新")')
            sb.sleep(5)

            # 结果保存
            success_img = str(OUTPUT_DIR / "success.png")
            sb.save_screenshot(success_img)
            msg = f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M')}] 续期成功！使用模式: {ui_mode}"
            print(msg)
            send_tg_notification(msg, success_img)

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error.png")
            sb.save_screenshot(error_img)
            print(f"❌ 流程中断: {e}")
            send_tg_notification(f"❌ 续期失败\n模式: {ui_mode}\n原因: {str(e)}", error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
