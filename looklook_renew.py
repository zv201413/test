#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import requests
import re
import random
from seleniumbase import SB

LOGIN_URL = "https://cloud.looklook.work/"

EMAIL = os.environ.get("ACC")
PASSWORD = os.environ.get("ACC_PWD")
TG_BOT_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_ID")

if not EMAIL or not PASSWORD:
    print("❌ 致命错误：未找到 ACC 或 ACC_PWD 环境变量！")
    sys.exit(1)

def send_tg_message(status_icon, status_text, extra_info=""):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    try:
        local_time = time.gmtime(time.time() + 8 * 3600)
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        text = f"🖥 LookLook.work 每日签到\n{status_icon} {status_text}\n{extra_info}\n时间: {current_time_str}"
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
    except:
        pass

_EXISTS_JS = "(function(){ var ts=document.querySelector('input[name=\"cf-turnstile-response\"]'); var challenge=document.querySelector('.cf-challenge,.challenge'); var pressHold=document.body.innerText.includes('Press and hold')||document.body.innerText.includes('按住'); return ts!==null||challenge!==null||pressHold; })()"

_SOLVED_JS = "(function(){ var i=document.querySelector('input[name=\"cf-turnstile-response\"]'); return !!(i&&i.value&&i.value.length>20); })()"

_COORDS_JS = "(function(){ var iframes=document.querySelectorAll('iframe'); for(var i=0;i<iframes.length;i++){var src=iframes[i].src||'';if(src.includes('cloudflare')||src.includes('turnstile')){var r=iframes[i].getBoundingClientRect();if(r.width>0&&r.height>0)return{cx:Math.round(r.x+30),cy:Math.round(r.y+r.height/2)}}}var inp=document.querySelector('input[name=\"cf-turnstile-response\"]');if(inp){var p=inp.parentElement;for(var j=0;j<5;j++){if(!p)break;var r=p.getBoundingClientRect();if(r.width>100&&r.height>30)return{cx:Math.round(r.x+30),cy:Math.round(r.y+r.height/2)};p=p.parentElement}}return null;})()"

_WININFO_JS = "(function(){return{sx:window.screenX||0,sy:window.screenY||0,oh:window.outerHeight,ih:window.innerHeight}})()"

def js_fill_input(sb, selector, text):
    safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
    sb.execute_script(f"(function(){{var el=document.querySelector('{selector}');if(!el)return;var nativeInputValueSetter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;if(nativeInputValueSetter){{nativeInputValueSetter.call(el,'{safe_text}')}}else{{el.value='{safe_text}'}}el.dispatchEvent(new Event('input',{{bubbles:true}}))}})()")

def _activate_window():
    for cls in ["chrome", "chromium", "Chrome"]:
        try:
            r = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", cls], capture_output=True, text=True, timeout=3)
            wids = [w for w in r.stdout.strip().split("\n") if w.strip()]
            if wids:
                subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]], timeout=3, stderr=subprocess.DEVNULL)
                time.sleep(0.2)
                return
        except:
            pass

def _xdotool_click(x, y):
    _activate_window()
    try:
        subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], timeout=3, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        subprocess.run(["xdotool", "click", "1"], timeout=2, stderr=subprocess.DEVNULL)
    except:
        os.system(f"xdotool mousemove {x} {y} click 1 2>/dev/null")

def _click_turnstile(sb):
    is_press = sb.execute_script("(function(){var t=document.body.innerText||'';return t.includes('Press and hold')||t.includes('按住')})()")
    if is_press:
        print("  ⚠️ 检测到 Press and Hold...")
        try:
            coords = sb.execute_script("(function(){var el=document.querySelector('.cf-challenge,.challenge');if(!el){var a=document.querySelectorAll('div,span,p');for(var i=0;i<a.length;i++){if(a[i].innerText&&a[i].innerText.includes('Press')){el=a[i];break}}}if(el){var r=el.getBoundingClientRect();return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)}}return null})()")
            if not coords:
                return
            try:
                wi = sb.execute_script(_WININFO_JS)
            except:
                wi = {"sx": 0, "sy": 0, "oh": 800, "ih": 768}
            bar = wi["oh"] - wi["ih"]
            ax = coords["cx"] + wi["sx"]
            ay = coords["cy"] + wi["sy"] + bar
            _activate_window()
            subprocess.run(["xdotool", "mousemove", "--sync", str(ax), str(ay)], timeout=3, stderr=subprocess.DEVNULL)
            time.sleep(0.2)
            subprocess.run(["xdotool", "mousedown", "1"], timeout=2, stderr=subprocess.DEVNULL)
            time.sleep(3)
            subprocess.run(["xdotool", "mouseup", "1"], timeout=2, stderr=subprocess.DEVNULL)
            print("  ✅ Press and Hold 完成")
        except Exception as e:
            print(f"  ⚠️ 错误: {e}")
        return
    
    try:
        coords = sb.execute_script(_COORDS_JS)
    except:
        print("  ⚠️ 获取坐标失败")
        return
    if not coords:
        print("  ⚠️ 无法定位")
        return
    try:
        wi = sb.execute_script(_WININFO_JS)
    except:
        wi = {"sx": 0, "sy": 0, "oh": 800, "ih": 768}
    bar = wi["oh"] - wi["ih"]
    ax = coords["cx"] + wi["sx"]
    ay = coords["cy"] + wi["sy"] + bar
    print(f"  🖱️ 点击 ({ax}, {ay})")
    _xdotool_click(ax, ay)

def handle_turnstile(sb):
    print("🔍 处理 CF 验证...")
    time.sleep(2)
    if sb.execute_script(_SOLVED_JS):
        print("  ✅ 已通过")
        return True
    for _ in range(3):
        time.sleep(0.5)
    for attempt in range(6):
        if sb.execute_script(_SOLVED_JS):
            print(f"  ✅ 通过 ({attempt+1})")
            return True
        time.sleep(0.3)
        _click_turnstile(sb)
        for _ in range(8):
            time.sleep(0.5)
            if sb.execute_script(_SOLVED_JS):
                print(f"  ✅ 通过 ({attempt+1})")
                return True
        print(f"  ⚠️ 第{attempt+1}次失败")
    print("  ❌ 失败")
    return False

def apply_zoom(sb, zoom="0.8"):
    try:
        print(f"🔧 设置 Transform 缩放 {zoom}...")
        sb.execute_script(f"""
            (function() {{
                document.body.style.transform = 'scale({zoom})';
                document.body.style.transformOrigin = '0 0';
                document.body.style.width = (100 / {zoom}) + '%';
                document.body.style.zoom = '{zoom}';
            }})();
        """)
    except:
        pass

def login(sb):
    print(f"🌐 打开登录页面: {LOGIN_URL}")
    sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=5)
    time.sleep(4)
    
    is_logged_in = sb.execute_script("return !!document.querySelector('.user-chip')")
    if is_logged_in:
        print("✅ 已经处于登录状态")
        return True

    print("🖱️ 打开登录弹窗...")
    try:
        sb.execute_script("openModal('login')")
        time.sleep(1)
    except:
        print("⚠️ 无法通过 JS 打开弹窗，尝试点击按钮...")
        sb.click('button.btn-login')
        time.sleep(1)

    print("📧 填写邮箱...")
    js_fill_input(sb, '#login-email', EMAIL)
    time.sleep(0.3)
    print("🔑 填写密码...")
    js_fill_input(sb, '#login-password', PASSWORD)
    time.sleep(1)
    
    if sb.execute_script(_EXISTS_JS):
        if not handle_turnstile(sb):
            sb.save_screenshot("login_turnstile_fail.png")
            return False
            
    print("🖱️ 提交登录...")
    sb.execute_script("doLogin()")
    
    for _ in range(15):
        time.sleep(1)
        if sb.execute_script("return !!document.querySelector('.user-chip')"):
            print("✅ 登录成功！")
            return True
        error_msg = sb.execute_script("return document.getElementById('auth-error').innerText")
        if error_msg and error_msg.strip():
            print(f"❌ 登录失败: {error_msg}")
            break
            
    sb.save_screenshot("login_failed.png")
    return False

def checkin(sb):
    print("\n" + "="*50)
    print(" 🚀 开始自动签到流程")
    print("="*50)

    apply_zoom(sb, "0.8")
    time.sleep(1)

    print("🚀 切换到签到面板...")
    try:
        sb.execute_script("switchTab('checkin')")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ 切换面板失败: {e}")
        sb.save_screenshot("switch_tab_error.png")

    print("🔍 检查签到状态...")
    btn_text = sb.execute_script("return document.getElementById('checkin-btn-text').innerText")
    if "已签到" in btn_text:
        print("ℹ️ 今日已签到")
    else:
        print("🖱️ 点击签到按钮...")
        try:
            sb.execute_script("doCheckIn()")
            time.sleep(5)
            sb.save_screenshot("after_checkin.png")
        except Exception as e:
            print(f"⚠️ 签到点击失败: {e}")
            sb.save_screenshot("checkin_error.png")

    print("🔍 验证结果...")
    try:
        points = sb.execute_script("return document.getElementById('points-num').innerText")
        streak = sb.execute_script("return document.getElementById('streak-label').innerText")
        
        result_info = f"当前积分: {points} | 连续签到: {streak}"
        print(f"✅ 结果: {result_info}")
        send_tg_message("✅", "签到成功", result_info)
        return True
    except Exception as e:
        print(f"⚠️ 读取结果失败: {e}")
        sb.save_screenshot("read_result_fail.png")
        send_tg_message("⚠️", "签到可能成功，但读取结果失败")
        return False

def main():
    print("="*50)
    print(" LookLook.work 自动签到")
    print("="*50)
    
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name == "schedule":
        delay_sec = random.randint(0, 18000)
        print(f"🕒 [定时任务] 随机延迟启动: {delay_sec // 3600} 小时 {(delay_sec % 3600) // 60} 分 {delay_sec % 60} 秒...")
        time.sleep(delay_sec)
    else:
        print(f"🚀 [手动/直接运行] 跳过随机延迟，立即开始流程...")

    proxy = os.environ.get("PROXY_URL", "").strip()
    opts = {"uc": True, "test": True, "headless": False, "proxy": None}
    
    if proxy:
        print(f"🔗 代理: http://127.0.0.1:8080")
        opts["proxy"] = "http://127.0.0.1:8080"
    
    with SB(**opts) as sb:
        sb.set_window_size(1920, 1080)
        print("✅ 启动")
        
        if login(sb):
            checkin(sb)
        else:
            print("❌ 登录失败")
            send_tg_message("❌", "登录失败")
            sys.exit(1)

if __name__ == "__main__":
    main()

