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
        st.subheader("➕ Add New Project")
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name*")
            customer_name = st.text_input("Customer Name*")
            category = st.selectbox("Category*", ["SERVICE", "PROJECT"])
            pic = st.text_input("PIC*")
        with col2:
            status = st.selectbox("Status*", ["Not Started", "On Going", "Completed", "Waiting BA"])
            date_start = st.date_input("Start Date*")
            date_end = st.date_input("End Date*")
            no_po = st.text_input("PO Number")
            no_bast = st.text_input("BAST Number")
        if st.form_submit_button("💾 Save Project"):
            if project_name and customer_name and category and pic and status and date_start and date_end:
                if date_start > date_end:
                    st.error("⚠️ Tanggal mulai harus sebelum tanggal selesai!")
                else:
                    try:
                        with sqlite3.connect('project_management.db') as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO projects (
                                    project_name, customer_name, category, pic, status,
                                    date_start, date_end, no_po, no_bast
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                project_name, customer_name, category, pic, status,
                                date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'),
                                no_po, no_bast
                            ))
                            conn.commit()
                        st.success("✅ Project added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error saat menambahkan proyek: {str(e)}")
            else:
                st.error("⚠️ Please fill all required fields (*)")

# EDIT PROJECT
def edit_project(project_id):
    if not st.session_state.get('is_admin', False):
        st.info("Fitur ini hanya untuk admin (MAA).")
        return
    if st.button("← Back to Board"):
        st.session_state['show_edit_form'] = False
        st.session_state['force_tab'] = "📋 Board"
        st.rerun()
    with st.form(key=f'edit_project_form_{project_id}'):
        st.subheader(f"✏️ Editing: {project[1]}")
        col1, col2 = st.columns(2)
        with col1:
            project_name = st.text_input("Project Name*", value=project[1])
            customer_name = st.text_input("Customer Name*", value=project[2])
            category = st.selectbox("Category*", ["SERVICE", "PROJECT"], 
                                  index=0 if project[3] == "SERVICE" else 1)
            pic = st.text_input("PIC*", value=project[4])
        with col2:
            status = st.selectbox("Status*", ["Not Started", "On Going", "Completed", "Waiting BA"], 
                                index=["Not Started", "On Going", "Completed", "Waiting BA"].index(project[5]))
            date_start = st.date_input("Start Date*", value=datetime.strptime(project[6], '%Y-%m-%d').date())
            date_end = st.date_input("End Date*", value=datetime.strptime(project[7], '%Y-%m-%d').date())
            no_po = st.text_input("PO Number", value=project[8])
            no_bast = st.text_input("BAST Number", value=project[9])
        if st.form_submit_button("💾 Update Project"):
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE projects SET
                        project_name=?, customer_name=?, category=?, pic=?, status=?,
                        date_start=?, date_end=?, no_po=?, no_bast=?
                    WHERE id=?
                ''', (
                    project_name, customer_name, category, pic, status,
                    date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d'),
                    no_po, no_bast, project_id
                ))
                conn.commit()
            st.success("✅ Project updated successfully!")
            st.session_state['show_edit_form'] = False
            st.rerun()

# DELETE PROJECT
def delete_project(project_id):
    if not st.session_state.get('is_admin', False):
        st.info("Fitur ini hanya untuk admin (MAA).")
        return
    if project:
        st.warning(f"⚠️ Are you sure you want to delete project: {project[1]}?")
        if st.button("🗑️ Confirm Delete"):
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path FROM project_files WHERE project_id=?", (project_id,))
                files = cursor.fetchall()
                for file in files:
                    if os.path.exists(file[0]):
                        os.remove(file[0])
                cursor.execute("DELETE FROM project_files WHERE project_id=?", (project_id,))
                cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
                conn.commit()
            st.success("✅ Project and all related files deleted successfully!")
            st.rerun()
    else:
        st.error("⚠️ Project not found")

# BOARD: PROJECT/SERVICE TAB
def view_projects_kanban():
    st.session_state['active_tab'] = "📋 Board"
    st.subheader("📋 Project Board", divider="blue")
    available_years = get_available_years()
    if not available_years:
        st.warning("No projects available")
        return
    current_year = datetime.now().strftime("%Y")
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = current_year if current_year in available_years else available_years[0]
    if st.session_state.selected_year not in available_years:
        st.session_state.selected_year = available_years[0]
    selected_year = st.selectbox(
        "Filter Year",
        available_years,
        index=available_years.index(st.session_state.selected_year),
        key='year_selector'
    )
    if selected_year != st.session_state.selected_year:
        st.session_state.selected_year = selected_year
        st.rerun()
    search_term = st.text_input("🔍 Search Projects...")
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE strftime('%Y', date_start) = ?
            ORDER BY date_start
        """, (selected_year,))
        projects = cursor.fetchall()
    if search_term:
        projects = [p for p in projects if search_term.lower() in p[1].lower() or search_term.lower() in p[2].lower()]
    
    projects_only = [p for p in projects if p[3] == "PROJECT"]
    services_only = [p for p in projects if p[3] == "SERVICE"]
    tab_project, tab_service = st.tabs(["📁 PROJECT", "🛠️ SERVICE"])
    with tab_project:
        st.markdown("### 📁 List Project")
        display_kanban(projects_only)
    with tab_service:
        st.markdown("### 🛠️ List Service")
        display_kanban(services_only)

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
    st.subheader("📅 Monthly Project Timeline", divider="blue")
    current_date = datetime.now()
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    col1, col2 = st.columns(2)
    with col1:
        selected_month = st.selectbox("Month", months, index=current_date.month-1)
    with col2:
        available_years = get_available_years() or [current_date.year]
        selected_year = st.selectbox("Year", available_years, index=len(available_years)-1)
    month_number = months.index(selected_month) + 1
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_name, customer_name, status, date_start, date_end 
            FROM projects 
            WHERE strftime('%m', date_start) = ? 
            AND strftime('%Y', date_start) = ?
            ORDER BY date_start
        """, (f"{month_number:02d}", selected_year))
        projects = cursor.fetchall()
    if not projects:
        st.info(f"📭 No projects in {selected_month} {selected_year}")
        return
    st.markdown(f"### 🗓️ Projects in {selected_month} {selected_year}")
    for project in projects:
        end_date = datetime.strptime(project[5], '%Y-%m-%d').date()
        days_left = (end_date - current_date.date()).days
        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{project[1]}**")
                st.caption(f"👤 {project[3]} | 🏢 {project[2]}")
                st.caption(f"📅 {project[4]} to {project[5]}")
            status_color = {
                "Not Started": "gray",
                "On Going": "blue",
                "Completed": "green",
                "Waiting BA": "orange"
            }.get(project[3], "gray")
            with cols[1]:
                st.markdown(f"""<div style='color:white; background-color:{status_color}; 
                              padding:0.2em 0.5em; border-radius:0.5em; text-align:center;'>
                              {project[3]}</div>""", unsafe_allow_html=True)
                
# MANAGE FILES
def manage_files(project_id=None):
    st.session_state['active_tab'] = "📂 Manage Files"
    BLOCKED_EXTENSIONS = ['.php', '.exe', '.bat', '.sh', '.js', '.py', '.jar']
    if project_id is None:
        available_years = get_available_years()
        if not available_years:
            st.warning("No projects available")
            return
        selected_year = st.selectbox("Filter by Year", available_years, index=0)
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, project_name, customer_name 
                FROM projects 
                WHERE strftime('%Y', date_start) = ?
                ORDER BY project_name
            """, (selected_year,))
            projects = cursor.fetchall()
        if not projects:
            st.info(f"No projects found for {selected_year}")
            return
        project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
        selected_project_name = st.selectbox("Select Project", list(project_options.keys()))
        selected_project_id = project_options[selected_project_name]
    else:
        selected_project_id = project_id
        project = get_project_details(selected_project_id)
        selected_project_name = f"{project[1]} - {project[2]}"
        st.write(f"Viewing files for: **{selected_project_name}**")
        if st.button("← Back to Board"):
            st.session_state.view_files_project = None
            st.session_state['force_tab'] = "📋 Board"
            st.rerun()
    tab1, tab2, tab_preview = st.tabs(["📋 Required Documents", "📂 Additional Files", "📑 File Preview"])
    # UPLOAD FORM Required
    with tab1:
        required_files = [
            "Form Request",
            "Form Tim Project",
            "Form Time Schedule",
            "SPK",
            "BAST",
            "Report"
        ]
        st.markdown("<span class='upload-doc-title'>📤 Upload Required Documents</span>", unsafe_allow_html=True)
        selected_category = st.selectbox("Document Type", required_files)
        uploaded_file = st.file_uploader(
            f"Choose {selected_category} file",
            type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'],
            key=f"uploader_{selected_project_id}_{selected_category}"
        )
        if st.session_state.get('is_admin', False):
            # uploader & upload button
            uploaded_file = st.file_uploader(...)
            if st.button("⬆️ Upload Required Document"):
                if not uploaded_file:
                st.error("Please select a file")
            else:
                file_extension = os.path.splitext(uploaded_file.name.lower())[1]
                if file_extension in BLOCKED_EXTENSIONS:
                    st.error(f"⚠️ File type {file_extension} is not allowed for security reasons")
                else:
                    directory = f"files/project_{selected_project_id}/required/"
                    os.makedirs(directory, exist_ok=True)
                    filepath = os.path.join(directory, uploaded_file.name)
                    try:
                        with open(filepath, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        with sqlite3.connect('project_management.db') as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO project_files (project_id, file_name, file_path, file_category) 
                                VALUES (?, ?, ?, ?)
                            """, (selected_project_id, uploaded_file.name, filepath, selected_category))
                            conn.commit()
                        st.success(f"✅ {selected_category} uploaded successfully!")
                    except Exception as e:
                        st.error(f"⚠️ Error saat mengupload file: {str(e)}")
                    st.rerun()
        st.markdown("### 📌 Existing Required Documents Status")
        for category in required_files:
            with sqlite3.connect('project_management.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT file_name 
                    FROM project_files 
                    WHERE project_id=? AND file_category=?
                """, (selected_project_id, category))
                uploaded_files = cursor.fetchall()
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
