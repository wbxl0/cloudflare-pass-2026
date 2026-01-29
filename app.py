import streamlit as st
import json
import os
import subprocess

CONFIG_FILE = "/app/output/tasks_config.json" # 存放在挂载的持久化目录

# --- 核心功能：保存与读取配置 ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_config(tasks):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# --- 初始化任务 ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = load_config()

# --- 主 UI 界面 ---
st.title("🤖 自动化任务管理器 (支持自动保存)")

# 遍历任务并创建输入框
new_task_list = []
for i, task in enumerate(st.session_state.tasks):
    with st.expander(f"任务: {task.get('name', '未命名')}", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        task['email'] = c1.text_input("账号", value=task.get('email', ''), key=f"e_{i}")
        task['password'] = c2.text_input("密码", type="password", value=task.get('password', ''), key=f"p_{i}")
        task['freq'] = c3.number_input("周期(天)", value=task.get('freq', 3), key=f"f_{i}")
        task['active'] = c4.checkbox("启用", value=task.get('active', True), key=f"a_{i}")
        new_task_list.append(task)

if st.button("💾 保存当前所有配置"):
    save_config(new_task_list)
    st.success("配置已保存到本地 JSON 文件，下次打开将自动加载！")

if st.button("🚀 统一点执行 (跑完所有流程)"):
    # 这里的逻辑会依次启动所有启用状态的任务
    for task in new_task_list:
        if task['active']:
            st.write(f"正在跑: {task['name']}...")
            # 这里的 env 设置会覆盖系统变量
            env = os.environ.copy()
            env["EMAIL"] = task['email']
            env["PASSWORD"] = task['password']
            subprocess.run(["xvfb-run", "python", task['script']], env=env)
