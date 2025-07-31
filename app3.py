import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
import zipfile
import io
from datetime import datetime
import base64
import streamlit_authenticator as stauth

# ================== LOGIN & ROLE SECTION ==================
# Ganti hashed_passwords ini dengan hasil stauth.Hasher(['password1',...]).generate()
hashed_passwords = [
    '$2b$12$1H1yJc8zRjY6l0sHUpuF7eCkjiZ3g4mVMWl1X0sZpFj1pTwkuh8YOa', # "maa12345"
    '$2b$12$2h5pG3e7Q8zJ6w7oG7pY7OQz8n6yV5nWl8pX2sZpFj1pTwkuh8YOa', # "esu12345"
    '$2b$12$3h6pK3e8Q9zJ7x8pG8qY8OQz9n7yW6nXm9qX3sZpFj1pTwkuh8YOa', # "ano12345"
    '$2b$12$4j7pL4e9R0zK8y9qH9rZ9OQz0o8yX7oYn0rY4sZpFj1pTwkuh8YOa', # "hgg12345"
    '$2b$12$5k8pM5f0S1zL9z0rI0sA0OQz1p9yY8pZo1sZ5sZpFj1pTwkuh8YOa', # "fmp12345"
    '$2b$12$6l9pN6g1T2zM0a1sJ1tB1OQz2q0yZ9qAp2tA6sZpFj1pTwkuh8YOa', # "yrc12345"
    '$2b$12$7m0pO7h2U3zN1b2tK2uC2OQz3r1yA0rBq3uB7sZpFj1pTwkuh8YOa', # "fon12345"
]
names = ['MAA', 'ESU', 'ANO', 'HGG', 'FMP', 'YRC', 'FON']
usernames = ['MAA', 'ESU', 'ANO', 'HGG', 'FMP', 'YRC', 'FON']

authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    'tscm_dashboard',   # cookie name
    'abcdef',           # any key
    cookie_expiry_days=7
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status is False:
    st.error('Username/password salah')
    st.stop()
if authentication_status is None:
    st.warning('Masukkan username dan password')
    st.stop()

authenticator.logout('Logout', 'sidebar')
is_admin = (username == "MAA")
st.session_state['is_admin'] = is_admin
st.session_state['logged_in'] = True
st.session_state['username'] = username

# ==========================================================

# INIT DB
def init_db():
    conn = sqlite3.connect('project_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            category TEXT NOT NULL,
            pic TEXT NOT NULL,
            status TEXT NOT NULL,
            date_start TEXT NOT NULL,
            date_end TEXT NOT NULL,
            no_po TEXT,
            no_bast TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_category TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')
    conn.commit()
    conn.close()

def get_all_projects():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        return cursor.fetchall()

def get_project_details(project_id):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        return cursor.fetchone()

def get_available_years():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT strftime('%Y', date_start) 
            FROM projects 
            ORDER BY date_start DESC
        """)
        return [row[0] for row in cursor.fetchall()]

def get_ongoing_projects_services():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project_name, category, pic
            FROM projects
            WHERE status = 'On Going'
            ORDER BY date_start DESC
        """)
        return cursor.fetchall()

# INIT DB & SESSION STATE
init_db()
if 'show_edit_form' not in st.session_state:
    st.session_state['show_edit_form'] = False
if 'edit_project_id' not in st.session_state:
    st.session_state['edit_project_id'] = None
if 'view_files_project' not in st.session_state:
    st.session_state.view_files_project = None
if 'mode_theme' not in st.session_state:
    st.session_state['mode_theme'] = "Dark Mode"
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "📋 Board"
if 'force_tab' not in st.session_state:
    st.session_state['force_tab'] = None

# Pilihan mode UI
mode = st.sidebar.radio("🌗 Pilih Mode Tampilan", ["Light Mode", "Dark Mode"], index=1 if st.session_state['mode_theme'] == "Dark Mode" else 0)
st.session_state['mode_theme'] = mode

if mode == "Light Mode":
    st.markdown("""
    <style>
    .stApp { background-color: #f6fbfc !important; color: #22223B !important; }
    ...
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="CISTECH", page_icon="📊", layout="wide")

# RUNNING TEXT (ON GOING PROJECT/SERVICE)
ongoing_list = get_ongoing_projects_services()
if ongoing_list:
    running_text = " | ".join(
        [f"{cat}: {name} (PIC: {pic})" for name, cat, pic in ongoing_list]
    )
else:
    running_text = "Tidak ada project/service yang sedang berjalan saat ini."

st.markdown(f"""
    <marquee behavior="scroll" direction="left" style="
        font-size:1.2em;
        font-weight:bold;
        color:#00BFFF;
        background:#f0f8ff;
        padding:8px 0;
        border-radius:8px;
        margin-bottom:10px;
        letter-spacing:1px;">
        {running_text}
    </marquee>
""", unsafe_allow_html=True)

# HEADER
st.image("cistech.png", width=545)
st.title("Dashboard Mapping Project TSCM")
st.title("ISO 9001-2015")

# ADD PROJECT
def add_project():
    if not st.session_state.get('is_admin', False):
        st.info("Fitur ini hanya untuk admin (MAA).")
        return
    with st.form(key='add_project_form'):
        ...
        # (form tambah project, sama seperti sebelumnya)

# EDIT PROJECT
def edit_project(project_id):
    if not st.session_state.get('is_admin', False):
        st.info("Fitur ini hanya untuk admin (MAA).")
        return
    ...
    # (form edit project, sama seperti sebelumnya)

# DELETE PROJECT
def delete_project(project_id):
    if not st.session_state.get('is_admin', False):
        st.info("Fitur ini hanya untuk admin (MAA).")
        return
    ...
    # (aksi hapus project, sama seperti sebelumnya)

# BOARD: PROJECT/SERVICE TAB
def view_projects_kanban():
    st.session_state['active_tab'] = "📋 Board"
    ...
    # (tidak perlu perubahan, hanya tombol edit project di dalam display_kanban nanti)

def display_kanban(projects):
    statuses = ["Not Started", "On Going", "Waiting BA", "Completed"]
    columns = st.columns(len(statuses))
    status_counts = {status: 0 for status in statuses}
    for project in projects:
        status = project[5]
        if status in status_counts:
            status_counts[status] += 1
    for idx, status in enumerate(statuses):
        with columns[idx]:
            st.subheader(f"{status} ({status_counts[status]})")
            filtered_projects = [p for p in projects if p[5] == status]
            for project in filtered_projects:
                with st.expander(f"📌 {project[1]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.session_state.get('is_admin', False):
                            if st.button(
                                "✏️ Edit Project", 
                                key=f"edit_btn_{project[0]}",
                                use_container_width=True
                            ):
                                st.session_state['edit_project_id'] = project[0]
                                st.session_state['show_edit_form'] = True
                                st.rerun()
                    with col2:
                        if st.button(
                            "📂 View Files",
                            key=f"view_files_{project[0]}",
                            use_container_width=True
                        ):
                            st.session_state.view_files_project = project[0]
                            st.session_state['force_tab'] = "📂 Manage Files"
                            st.rerun()
                    ...

# TIMELINE
def view_timeline():
    st.session_state['active_tab'] = "📅 Timeline"
    ...
    # (tidak perlu perubahan)

# MANAGE FILES
def manage_files(project_id=None):
    st.session_state['active_tab'] = "📂 Manage Files"
    ...
    # UPLOAD FORM Required
    with tab1:
        ...
        if st.session_state.get('is_admin', False):
            # uploader & upload button
            uploaded_file = st.file_uploader(...)
            if st.button("⬆️ Upload Required Document"):
                ...
        else:
            st.info("Hanya admin (MAA) yang dapat upload dokumen.")
        ...
    # UPLOAD FORM Additional
    with tab2:
        ...
        if st.session_state.get('is_admin', False):
            # uploader & upload button
            ...
        else:
            st.info("Hanya admin (MAA) yang dapat upload file tambahan.")
        # TOMBOL DELETE FILE
        ...
        with cols[2]:
            if st.session_state.get('is_admin', False):
                if st.button("🗑️", key=f"del_add_{file[0]}_{idx}"):
                    ...
            # User non-admin tidak bisa hapus file, tombol tidak tampil
    # TAB PREVIEW Delete button
    with tab_preview:
        ...
        with col4:
            if st.session_state.get('is_admin', False):
                if st.button("❌ Delete", key=f"delete_{file_id}"):
                    ...
            # User non-admin tidak bisa hapus file

# CHART
def dashboard_line_chart():
    st.session_state['active_tab'] = "📈 Grafik Proyek"
    ...

# MAIN APP FUNCTION
def main_app():
    ...
    if st.session_state['show_edit_form']:
        edit_project(st.session_state['edit_project_id'])
    elif st.session_state.view_files_project:
        ...
    else:
        # Tab list, hanya tampilkan fitur CRUD ke admin
        tab_names = [
            "📈 Grafik Proyek",
            "📋 Board", 
            "📅 Timeline"
        ]
        if st.session_state.get('is_admin', False):
            tab_names += ["➕ Add Project", "✏️ Edit Project", "🗑️ Delete Project"]
        tab_names += ["📂 Manage Files"]
        tabs = st.tabs(tab_names)
        active_index = tab_names.index(st.session_state['active_tab']) if st.session_state['active_tab'] in tab_names else 1
        tabs[active_index].write("")
        with tabs[0]:
            dashboard_line_chart()
        with tabs[1]:
            view_projects_kanban()
        with tabs[2]:
            view_timeline()
        if st.session_state.get('is_admin', False):
            with tabs[3]:
                add_project()
            with tabs[4]:
                st.subheader("✏️ Edit Project")
                projects = get_all_projects()
                if projects:
                    project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
                    selected_project = st.selectbox("Select Project to Edit", list(project_options.keys()))
                    edit_project(project_options[selected_project])
                else:
                    st.info("No projects available to edit")
            with tabs[5]:
                st.subheader("🗑️ Delete Project")
                projects = get_all_projects()
                if projects:
                    project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
                    selected_project = st.selectbox("Select Project to Delete", list(project_options.keys()))
                    delete_project(project_options[selected_project])
                else:
                    st.info("No projects available to delete")
            with tabs[6]:
                manage_files()
        else:
            with tabs[3]:
                manage_files()

# RUN THE APP
if __name__ == "__main__":
    main_app()
