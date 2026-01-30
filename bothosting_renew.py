import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from seleniumbase import SB
from loguru import logger

# ==========================================
# 1. 严格按照仓库 API 逻辑进行函数导入 (完全不改)
# ==========================================
try:
    from bypass import bypass_cloudflare as api_core_1
    from simple_bypass import bypass_cloudflare as api_core_2
    from simple_bypass import bypass_parallel as api_core_3
    from bypass_seleniumbase import bypass_logic as api_core_4
    logger.info("📡 核心 API 插件已成功挂载至主程序")
except Exception as e:
    logger.error(f"🚨 API 加载失败: {e}")

# ==========================================
# 2. 高科技 TGUI 功能 (北京时间 + 单次发送)
# ==========================================
def send_tg_notification(status, message, photo_path=None):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): return
    
    bj_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    emoji = "✅" if "成功" in status else "⚠️" if "未到期" in status else "❌"
    
    formatted_msg = (
        f"{emoji} **矩阵自动化续期报告**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **账户**: `{os.environ.get('EMAIL', 'Unknown')}`\n"
        f"📡 **状态**: {status}\n"
        f"📝 **详情**: {message}\n"
        f"🕒 **北京时间**: `{bj_time}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': formatted_msg, 'parse_mode': 'Markdown'}, files={'photo': f})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': formatted_msg, 'parse_mode': 'Markdown'})
    except Exception as e: logger.error(f"TG通知失败: {e}")

# ==========================================
# 3. 自动化续期主流程 (集成远程画面推流)
# ==========================================
def run_auto_renew():
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    ui_mode = os.environ.get("BYPASS_MODE", "1. 基础单次模式")
    
    login_url = "https://bot-hosting.net/login"
    OUTPUT_DIR = Path("/app/output")
    # 画面同步路径与 UI 对应
    LIVE_IMG = str(OUTPUT_DIR / "live_view.png")
    # 缓存路径与 UI 对应
    DATA_DIR = "/app/output/browser_cache"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 核心：使用 data_dir 开启持久化缓存记录
    with SB(uc=True, xvfb=True, data_dir=DATA_DIR) as sb:
        try:
            # ---- [步骤 A] 启动推流循环 (用于手动模式) ----
            sb.uc_open_with_reconnect(login_url, 10)
            
            # 持续推流画面给 UI (如果是手动模式运行)
            sb.save_screenshot(LIVE_IMG) 
            logger.info("已启动实时画面同步至 live_view.png")

            # ---- [步骤 B] 检查 Cookies 是否已登录 ----
            if "panel" in sb.get_current_url():
                logger.success("检测到有效缓存，自动跳过验证码")
                status_msg = "通过缓存直接进入"
            else:
                # ---- [步骤 C] 核心：API 调用与 Discord 授权 ----
                # 按照原逻辑点击 Discord 登录
                if sb.is_element_visible('a[href*="discord"]'):
                    sb.click('a[href*="discord"]')
                    sb.sleep(5)
                
                # 画面更新
                sb.save_screenshot(LIVE_IMG)
                
                # 调用你指定的 API
                current_url = sb.get_current_url()
                if "1." in ui_mode: result = api_core_1(current_url)
                elif "2." in ui_mode: result = api_core_2(current_url, proxy=os.environ.get("PROXY"))
                elif "3." in ui_mode: result = api_core_3(url=current_url, proxy_file="proxy.txt", batch_size=3)
                elif "4." in ui_mode: 
                    api_core_4(sb)
                    result = {"success": True}

                # 处理 hCaptcha 复选框
                if sb.is_element_visible('iframe[title*="hCaptcha"]'):
                    sb.switch_to_frame('iframe[title*="hCaptcha"]')
                    sb.click('#checkbox') 
                    sb.switch_to_default_content()
                    sb.save_screenshot(LIVE_IMG) # 再次更新画面

                sb.uc_gui_click_captcha()
                logger.info("验证识别中，进入 20 秒稳定缓冲期...")
                sb.sleep(20) # 一个字没动
                
                # 再次推流，让你在 UI 看到是否需要输入账号
                sb.save_screenshot(LIVE_IMG)

                # 注入凭据
                if sb.is_element_visible('input[name="email"]'):
                    sb.type('input[name="email"]', email)
                    sb.type('input[name="password"]', password)
                    sb.click('button[type="submit"]')
                    sb.sleep(10)
                
                # 授权确认
                if "authorize" in sb.get_current_url() or sb.is_element_visible('button:contains("Authorize")'):
                    sb.click('button:contains("Authorize")')
                    sb.sleep(8)
                
                status_msg = "完成 Discord 授权登录"

            # ---- [步骤 D] 结果保存与通知 ----
            sb.uc_open_with_reconnect("https://bot-hosting.net/panel", 10)
            sb.sleep(5)
            sb.save_screenshot(LIVE_IMG) # 最终画面

            final_img = str(OUTPUT_DIR / "bothosting_final.png")
            sb.save_screenshot(final_img)
            
            if "panel" in sb.get_current_url():
                send_tg_notification("保活成功 ✅", f"Bot-Hosting {status_msg}，Session 已缓存。", final_img)
            else:
                send_tg_notification("未到期 ⚠️", "目前处于登录流程中，请查看 UI 画面是否卡在验证码。", final_img)

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error.png")
            sb.save_screenshot(error_img)
            send_tg_notification("执行异常 ❌", f"任务中断: `{str(e)}`", error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
