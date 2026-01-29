import streamlit as st
import json
import os
import subprocess

# 配置文件存放在持久化目录
CONFIG_FILE = "/app/output/tasks_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return [{"name": "Katabump续期", "script": "katabump_renew.py", "mode": "单浏览器模式", "email": "", "password": "", "freq": 3, "active": True}]

def save_config(tasks):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

st.set_page_config(page_title="自动化任务管理器", layout="wide")
st.title("🤖 多项目自动化续期管理中心")

if 'tasks' not in st.session_state:
    st.session_state.tasks = load_config()

# --- 侧边栏：添加新项目 ---
with st.sidebar:
    st.header("➕ 添加新项目")
    new_name = st.text_input("项目备注名称")
    available_scripts = ["katabump_renew.py", "bypass.py", "bypass_seleniumbase.py", "simple_bypass.py"]
    new_script = st.selectbox("关联脚本文件", available_scripts)
    if st.button("添加至列表"):
        st.session_state.tasks.append({
            "name": new_name, "script": new_script, 
            "mode": "单浏览器模式", "email": "", "password": "", "freq": 3, "active": True
        })
        save_config(st.session_state.tasks)
        st.success("已添加！")

# --- 主界面：配置区 ---
updated_tasks = []
st.subheader("📋 任务列表 (配置自动保存)")

for i, task in enumerate(st.session_state.tasks):
    with st.expander(f"项目: {task['name']} (脚本: {task['script']})", expanded=True):
        col1, col2, col3, col4, col5 = st.columns([1, 1.5, 2, 2, 0.5])
        
        task['active'] = col1.checkbox("启用", value=task.get('active', True), key=f"active_{i}")
        
        # 模式选择同步到配置
        mode_options = ["单浏览器模式", "SB增强模式", "并行竞争模式"]
        current_mode = task.get('mode', "单浏览器模式")
        default_idx = mode_options.index(current_mode) if current_mode in mode_options else 0
        task['mode'] = col2.selectbox("验证模式", mode_options, index=default_idx, key=f"mode_{i}")
        
        task['email'] = col3.text_input("账号", value=task.get('email', ''), key=f"email_{i}")
        task['password'] = col4.text_input("密码", type="password", value=task.get('password', ''), key=f"pw_{i}")
        
        if col5.button("🗑️", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_config(st.session_state.tasks)
            st.rerun()
        updated_tasks.append(task)

if st.button("💾 保存所有配置"):
    save_config(updated_tasks)
    st.success("✅ 配置已保存！")

st.divider()

# --- 手动执行区 ---
if st.button("🚀 统一点执行 (一键跑通)"):
    with st.status("正在运行...", expanded=True) as status:
        for task in updated_tasks:
            if task['active']:
                st.write(f"正在运行: {task['name']} (模式: {task['mode']})...")
                env = os.environ.copy()
                env["EMAIL"] = task['email']
                env["PASSWORD"] = task['password']
                env["BYPASS_MODE"] = task['mode']  # 注入模式变量
                
                cmd = ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "python", task['script']]
                process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                
                out_box = st.empty()
                full_out = ""
                for line in process.stdout:
                    full_out += line
                    out_box.code(full_out)
                process.wait()
        status.update(label="✨ 全部手动任务执行完毕", state="complete")
