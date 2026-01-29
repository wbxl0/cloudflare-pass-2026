import os
import time
from seleniumbase import SB

def execute_renew():
    # 从 Zeabur 环境变量读取
    url = "https://dashboard.katabump.com/login"
    target_id_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")

    if not email or not password:
        return "❌ 错误：请在 Zeabur 环境变量中设置 EMAIL 和 PASSWORD"

    # 启动带有虚拟显示器的反检测浏览器
    with SB(uc=True, xvfb=True) as sb:
        try:
            # ---- 第一步：访问登录页并过“大门”验证 ----
            sb.uc_open_with_reconnect(url, 5)
            sb.uc_gui_click_captcha() 
            
            # ---- 第二步：执行登录 ----
            sb.type("#email", email)
            sb.type("#password", password)
            sb.click('button:contains("登录")') 
            sb.sleep(3)

            # ---- 第三步：跳转到特定的 See 页面 ----
            sb.uc_open_with_reconnect(target_id_url, 5)
            
            # ---- 第四步：触发续期弹窗 ----
            sb.scroll_to('button[data-bs-target="#renew-modal"]')
            sb.click('button[data-bs-target="#renew-modal"]')
            sb.sleep(2)

            # ---- 第五步：处理续期弹窗中的人机验证 ----
            sb.uc_gui_click_captcha() 
            sb.sleep(2)

            # ---- 第六步：点击最后的“更新”按钮 ----
            sb.click('button:contains("更新")')
            
            return f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 续期指令已发送！"
        except Exception as e:
            # 失败自动截图
            sb.save_screenshot("/app/output/error.png")
            return f"❌ 运行失败: {str(e)}"
