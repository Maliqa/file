import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import os
import pandas as pd
import plotly.express as px
import zipfile
import io
from datetime import datetime
import base64

# ========== CUSTOM WINDOWS STYLE ===============
st.set_page_config(page_title="CISTECH", page_icon="🪟", layout="wide")
st.markdown("""
<style>
.stApp { background-color: #e3ebf5 !important; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #205295 0%, #144272 100%);
    color: #fff;
}
[data-testid="stSidebar"] .css-1wvake5, /* Option menu hover/selected */
[data-testid="stSidebar"] .css-1whn0k4 {
    background: none !important;
}
.stButton > button, .stDownloadButton > button, .stDownloadButton > a {
    background: #205295 !important; color: #fff !important; font-weight: 600 !important;
    border-radius: 8px !important; border: none !important;
}
.stForm, .stExpander, .stContainer {
    background: #fff !important; border-radius: 16px !important;
    box-shadow: 0 3px 18px #20529522;
    padding: 20px;
}
.stTabs [role="tab"] {
    border-radius: 8px 8px 0 0 !important; background: #f0f6ff !important;
    color: #205295 !important;
}
.stTabs [aria-selected="true"] {
    background: #205295 !important; color: #fff !important;
}
div[data-testid="stVerticalBlock"]>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div>div {
    margin-bottom: 0px !important;  /* Card spacing fix */
}
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR WINDOWS MENU ==========
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/48/Windows_logo_-_2021.svg", width=64)
    st.title("CISTECH Project")
    selected = option_menu(
        None,
        [
            "Board", "Timeline", "Add Project",
            "Edit Project", "Delete Project", "Manage Files"
        ],
        icons=[
            "grid-1x2-fill", "calendar2-week", "plus-circle",
            "pencil-square", "trash", "folder2-open"
        ],
        menu_icon="windows", default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#205295"},
            "icon": {"color": "white", "font-size": "22px"},
            "nav-link": {"font-size": "17px", "text-align": "left", "margin":"0px", "--hover-color": "#144272"},
            "nav-link-selected": {"background-color": "#144272"},
        }
    )
    st.markdown("""
    <div style='position:fixed;bottom:20px;left:20px;'>
        <img src='https://upload.wikimedia.org/wikipedia/commons/4/48/Windows_logo_-_2021.svg' width='26'>
        <span style='color:#fff;font-size:14px;margin-left:8px;'>Windows Menu</span>
    </div>
    """, unsafe_allow_html=True)

# ==================== DATABASE =====================

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

# ========== INIT DB & SESSION STATE ==========
init_db()
if 'show_edit_form' not in st.session_state: st.session_state['show_edit_form'] = False
if 'edit_project_id' not in st.session_state: st.session_state['edit_project_id'] = None
if 'view_files_project' not in st.session_state: st.session_state.view_files_project = None

# ========== RUNNING TEXT ==========
ongoing_list = get_ongoing_projects_services()
if ongoing_list:
    running_text = " | ".join(
        [f"{cat}: {name} (PIC: {pic})" for name, cat, pic in ongoing_list]
    )
else:
    running_text = "Tidak ada project/service yang sedang berjalan saat ini."

st.markdown(f"""
    <marquee behavior="scroll" direction="left" style="
        font-size:1.1em;
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

# ========== HEADER ==========
st.image("cistech.png", width=300)
st.markdown("<h2 style='color:#205295'>Dashboard Mapping Project TSCM</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#144272'>ISO 9001-2015</h4>", unsafe_allow_html=True)

# ========== ADD PROJECT ==========
def add_project():
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
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error saat menambahkan proyek: {str(e)}")
            else:
                st.error("⚠️ Please fill all required fields (*)")

# ========== EDIT PROJECT ==========
def edit_project(project_id):
    project = get_project_details(project_id)
    if not project:
        st.error("⚠️ Project not found!")
        return
    if st.button("← Back to Board"):
        st.session_state['show_edit_form'] = False
        st.experimental_rerun()
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
            st.experimental_rerun()

# ========== DELETE PROJECT ==========
def delete_project(project_id):
    project = get_project_details(project_id)
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
            st.experimental_rerun()
    else:
        st.error("⚠️ Project not found")

# ========== BOARD ==========
def view_projects_kanban():
    st.subheader("🗂️ Project Board")
    available_years = get_available_years()
    if not available_years:
        st.warning("No projects available")
        return
    current_year = datetime.now().strftime("%Y")
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = current_year if current_year in available_years else available_years[0]
    selected_year = st.selectbox(
        "Filter Year",
        available_years,
        index=available_years.index(st.session_state.selected_year),
        key='year_selector'
    )
    st.session_state.selected_year = selected_year
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
        st.markdown("#### 📁 List Project")
        display_kanban(projects_only)
    with tab_service:
        st.markdown("#### 🛠️ List Service")
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
                st.markdown(f"""
                <div style='background:#fff;border-radius:10px;box-shadow:0 2px 10px #20529522;padding:16px;margin-bottom:12px;'>
                  <b>{project[1]}</b><br>
                  <span style='color:#205295;'>Customer:</span> {project[2]}<br>
                  <span style='color:#205295;'>PIC:</span> {project[4]}<br>
                  <span style='color:#205295;'>Status:</span> {project[5]}<br>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_btn_{project[0]}"):
                        st.session_state['edit_project_id'] = project[0]
                        st.session_state['show_edit_form'] = True
                        st.experimental_rerun()
                with col2:
                    if st.button("📂 Files", key=f"view_files_{project[0]}"):
                        st.session_state.view_files_project = project[0]
                        st.experimental_rerun()
                st.progress({
                    "Not Started": 0,
                    "On Going": 50,
                    "Waiting BA": 80,
                    "Completed": 100
                }.get(project[5], 0))
                st.write("</div>", unsafe_allow_html=True)

# ========== TIMELINE ==========
def view_timeline():
    st.subheader("📅 Monthly Project Timeline")
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

# ========== MANAGE FILES ==========
def manage_files(project_id=None):
    st.subheader("📂 Manage Files")
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
            st.experimental_rerun()
    tab1, tab2, tab_preview = st.tabs(["📋 Required Documents", "📂 Additional Files", "📑 File Preview"])
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
                    st.experimental_rerun()
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
            if uploaded_files:
                st.markdown(f"**{category}**: ✅ (Uploaded)")
            else:
                st.markdown(f"**{category}**: ❌ (Not Uploaded)")
    with tab2:
        st.markdown("### 📂 Upload Additional Files")
        custom_category = st.text_input("Custom File Name*",
                    placeholder="e.g. Meeting Notes, Contract Draft",
                    help="Nama deskriptif untuk file ini")
        uploaded_custom_file = st.file_uploader(
            f"Choose additional file for {selected_project_name} (Max 10MB)",
            type=[
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 
                'jpg', 'jpeg', 'png', 'txt', 'ppt', 'pptx'
            ],
            key=f"additional_{selected_project_id}"
        )
        if st.button("⬆️ Upload Additional File"):
            if not custom_category:
                st.error("Please enter a file name")
            elif not uploaded_custom_file:
                st.error("Please select a file")
            else:
                file_name = uploaded_custom_file.name.lower()
                file_extension = os.path.splitext(file_name)[1]
                if file_extension in BLOCKED_EXTENSIONS:
                    st.error(f"⚠️ File type {file_extension} is not allowed for security reasons")
                elif uploaded_custom_file.size > 10 * 1024 * 1024:
                    st.error("File size exceeds 10MB limit")
                else:
                    directory = f"files/project_{selected_project_id}/additional/"
                    os.makedirs(directory, exist_ok=True)
                    safe_filename = "".join(
                        c for c in uploaded_custom_file.name 
                        if c.isalnum() or c in ('.', '-', '_')
                    ).rstrip()
                    filepath = os.path.join(directory, safe_filename)
                    with open(filepath, "wb") as f:
                        f.write(uploaded_custom_file.getbuffer())
                    with sqlite3.connect('project_management.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO project_files 
                            (project_id, file_name, file_path, file_category) 
                            VALUES (?, ?, ?, ?)
                        """, (
                            selected_project_id, 
                            safe_filename, 
                            filepath, 
                            f"Additional: {custom_category}"
                        ))
                        conn.commit()
                    st.success(f"✅ File '{custom_category}' uploaded successfully!")
                    st.experimental_rerun()
        st.markdown("### 📌 Existing Additional Files")
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, file_name, file_path, file_category 
                FROM project_files 
                WHERE project_id=? AND file_category LIKE 'Additional:%'
                ORDER BY file_category
            """, (selected_project_id,))
            additional_files = cursor.fetchall()
        if additional_files:
            for idx, file in enumerate(additional_files):
                cols = st.columns([5, 1, 1])
                with cols[0]:
                    display_name = file[3].replace("Additional: ", "")
                    st.markdown(f"**{display_name}**: `{file[1]}`")
                    if os.path.exists(file[2]):
                        size = os.path.getsize(file[2]) / 1024
                        st.caption(f"{size:.2f} KB")
                with cols[1]:
                    if os.path.exists(file[2]):
                        st.download_button(
                            label="Download",
                            data=open(file[2], "rb").read(),
                            file_name=file[1],
                            mime="application/octet-stream",
                            key=f"dl_add_{file[0]}_{idx}"
                        )
                    else:
                        st.warning("Missing")
                with cols[2]:
                    if st.button("🗑️", key=f"del_add_{file[0]}_{idx}"):
                        try:
                            if os.path.exists(file[2]):
                                os.remove(file[2])
                            with sqlite3.connect('project_management.db') as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    DELETE FROM project_files 
                                    WHERE id=?
                                """, (file[0],))
                                conn.commit()
                            st.success("✅ File deleted successfully!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {str(e)}")
        else:
            st.info("No additional files uploaded yet")
    with tab_preview:
        st.markdown(f"### 📑 File Preview: {selected_project_name}")
        col1, col2 = st.columns(2)
        with col1:
            file_type = st.selectbox(
                "Filter File Type",
                ["All", "Required Documents", "Additional Files"],
                key="file_type_filter"
            )
        with col2:
            search_query = st.text_input("🔍 Search by filename")
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            query = """
                SELECT file_name, file_path, file_category, id 
                FROM project_files 
                WHERE project_id=?
            """
            params = [selected_project_id]
            if file_type == "Required Documents":
                query += " AND file_category NOT LIKE 'Additional:%'"
            elif file_type == "Additional Files":
                query += " AND file_category LIKE 'Additional:%'"
            if search_query:
                query += " AND file_name LIKE ?"
                params.append(f"%{search_query}%")
            cursor.execute(query, params)
            files = cursor.fetchall()
        if files:
            if st.button("🗂️ Download All Files as ZIP"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in files:
                        file_name, file_path, file_category, _ = file
                        if os.path.exists(file_path):
                            zipf.write(file_path, arcname=file_name)
                        else:
                            st.warning(f"File not found: {file_name}")
                zip_buffer.seek(0)
                st.download_button(
                    label="⬇️ Download ZIP Now",
                    data=zip_buffer,
                    file_name=f"{selected_project_name}_files.zip",
                    mime="application/zip",
                    key="download_all_zip"
                )
        if not files:
            st.info("No files found matching your criteria")
        else:
            for idx, file in enumerate(files):
                file_name, file_path, file_category, file_id = file
                file_ext = os.path.splitext(file_name)[1].lower()
                with st.expander(f"📄 {file_name} ({file_category})"):
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                    with col1:
                        st.markdown(f"**Type:** {file_category}")
                        if os.path.exists(file_path):
                            st.markdown(f"**Size:** {os.path.getsize(file_path) / 1024:.2f} KB")
                        else:
                            st.markdown("**Size:** File missing")
                    with col2:
                        if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.txt', '.xls', '.xlsx']:
                            if st.button("👁️ Preview", key=f"preview_{file_id}"):
                                st.session_state['preview_file'] = file_path
                    with col3:
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download",
                                    data=f,
                                    file_name=file_name,
                                    key=f"download_{file_id}"
                                )
                        else:
                            st.error("File missing")
                    with col4:
                        if st.button("❌ Delete", key=f"delete_{file_id}"):
                            with st.spinner("Deleting..."):
                                try:
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                    with sqlite3.connect('project_management.db') as conn:
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "DELETE FROM project_files WHERE id=?",
                                            [file_id]
                                        )
                                        conn.commit()
                                    st.success(f"Deleted: {file_name}")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    # PREVIEW BLOCK (sudah support Excel)
                    if st.session_state.get('preview_file') == file_path:
                        st.markdown("---")
                        st.markdown("### File Preview")
                        if not os.path.exists(file_path):
                            st.error("File not found on server")
                        elif file_ext == '.pdf':
                            with open(file_path, "rb") as f:
                                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                                pdf_display = f"""
                                    <iframe 
                                        src="data:application/pdf;base64,{base64_pdf}" 
                                        width="100%" 
                                        height="500px" 
                                        style="border:1px solid #eee;"
                                    ></iframe>
                                """
                                st.markdown(pdf_display, unsafe_allow_html=True)
                        elif file_ext in ['.jpg', '.jpeg', '.png']:
                            st.image(file_path, use_column_width=True)
                        elif file_ext == '.txt':
                            with open(file_path, "r") as f:
                                st.text_area("Content", f.read(), height=200)
                        elif file_ext in ['.xls', '.xlsx']:
                            try:
                                df = pd.read_excel(file_path)
                                st.dataframe(df)
                            except Exception as e:
                                st.error(f"Gagal preview Excel: {str(e)}")
                        else:
                            st.warning("Preview not available for this file type")

# ========== MAIN APP ==========
def main_app():
    if st.session_state['show_edit_form']:
        edit_project(st.session_state['edit_project_id'])
    elif st.session_state.view_files_project:
        project_id = st.session_state.view_files_project
        project_details = get_project_details(project_id)
        if project_details:
            st.subheader(f"📂 Files for: {project_details[1]}")
            manage_files(project_id=project_id)
        else:
            st.error("Project not found")
            st.session_state.view_files_project = None
    else:
        if selected == "Board":
            view_projects_kanban()
        elif selected == "Timeline":
            view_timeline()
        elif selected == "Add Project":
            add_project()
        elif selected == "Edit Project":
            st.subheader("✏️ Edit Project")
            projects = get_all_projects()
            if projects:
                project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
                selected_project = st.selectbox("Select Project to Edit", list(project_options.keys()))
                edit_project(project_options[selected_project])
            else:
                st.info("No projects available to edit")
        elif selected == "Delete Project":
            st.subheader("🗑️ Delete Project")
            projects = get_all_projects()
            if projects:
                project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
                selected_project = st.selectbox("Select Project to Delete", list(project_options.keys()))
                delete_project(project_options[selected_project])
            else:
                st.info("No projects available to delete")
        elif selected == "Manage Files":
            manage_files()

# ========== RUN THE APP ==========
if __name__ == "__main__":
    main_app()