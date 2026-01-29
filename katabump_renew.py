import os
import time
import requests
from seleniumbase import SB

def send_tg_notification(message, photo_path=None):
    """发送 Telegram 消息和截图"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[!] 未配置 TG 变量，跳过通知")
        return

    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': message}, 
                              files={'photo': photo})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': message})
    except Exception as e:
        print(f"[!] TG 通知发送失败: {e}")

def run_auto_renew():
    # 从 Zeabur 环境变量读取
    url = "https://dashboard.katabump.com/login"
    target_id_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")

    # 启动带有虚拟显示器的反检测浏览器
    with SB(uc=True, xvfb=True) as sb:
        # ---- 第一步：访问登录页并过“大门”验证 ----
        sb.uc_open_with_reconnect(url, 5)
        sb.uc_gui_click_captcha() # 点击首页可能存在的 CF 验证
        
        # ---- 第二步：执行登录 ----
        sb.type("#email", email)
        sb.type("#password", password)
        sb.click('button:contains("登录")') # 匹配你提到的“登录”字体按钮
        sb.sleep(3)

        # ---- 第三步：跳转到特定的 See 页面 ----
        sb.uc_open_with_reconnect(target_id_url, 5)
        
        # ---- 第四步：触发续期弹窗 ----
        # 页面下滑并寻找 Renew 按钮
        sb.scroll_to('button[data-bs-target="#renew-modal"]')
        sb.click('button[data-bs-target="#renew-modal"]')
        sb.sleep(2)

        # ---- 第五步：处理续期弹窗中的人机验证 ----
        # 原作者的逻辑会在此处自动寻找并尝试点击验证框
        sb.uc_gui_click_captcha() 
        sb.sleep(2)

        # ---- 第六步：点击最后的“更新”按钮 ----
        sb.click('button:contains("更新")')
        
        # 保存成功截图
        success_screenshot = "/app/output/success_renew.png"
        os.makedirs("/app/output", exist_ok=True)
        sb.save_screenshot(success_screenshot)
        
        success_msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 续期指令已发送！"
        print(success_msg)
        
        # 发送 TG 通知
        send_tg_notification(success_msg, success_screenshot)
        
        sb.sleep(5) # 留出时间确认请求发送完毕

if __name__ == "__main__":
    run_auto_renew()
