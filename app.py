import streamlit as st
import sqlite3
import os
import zipfile
import io
from datetime import datetime

# Initialize database
st.set_page_config(page_title="CISTECH", page_icon="📊", layout="wide")

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

# Database functions
def get_all_projects():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects")
        return cursor.fetchall()

def get_projects_by_year(year):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE strftime('%Y', date_start) = ? 
            OR strftime('%Y', date_end) = ?
        """, (str(year), str(year)))
        return cursor.fetchall()

def get_ongoing_projects():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE status IN ('On Going', 'Waiting BA')
            ORDER BY date_end ASC
        """)
        return cursor.fetchall()

def get_project_details(project_id):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        return cursor.fetchone()

def search_projects(search_term):
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects 
            WHERE project_name LIKE ? 
            OR customer_name LIKE ?
        """, ('%' + search_term + '%', '%' + search_term + '%'))
        return cursor.fetchall()

def get_available_years():
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT strftime('%Y', date_start) 
            FROM projects 
            ORDER BY date_start DESC
        """)
        return [row[0] for row in cursor.fetchall()]

# Header
st.image("cistech.png", width=450)
st.title("Dashboard Mapping Project TSCM")
st.title("ISO 9001-2015")

# Add Project
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
            else:
                st.error("⚠️ Please fill all required fields (*)")

def edit_project(project_id):
    project = get_project_details(project_id)
    if not project:
        st.error("⚠️ Project not found!")
        return
    
    if st.button("← Back to Board"):
        st.session_state['show_edit_form'] = False
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

# Delete Project
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
    else:
        st.error("⚠️ Project not found")

# Timeline View
def view_timeline():
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

# Kanban View
def view_projects_kanban():
    st.subheader("📋 Project Board", divider="blue")
    
    available_years = get_available_years()
    if not available_years:
        st.warning("No projects available")
        return
    
    selected_year = st.selectbox("Filter Year", available_years, index=len(available_years)-1)
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
                    # Edit button inside the card
                    if st.button(
                        "✏️ Edit Project", 
                        key=f"edit_btn_{project[0]}_{status}",
                        type="secondary",
                        use_container_width=True
                    ):
                        st.session_state['edit_project_id'] = project[0]
                        st.session_state['show_edit_form'] = True
                        st.rerun()
                    
                    # Project info
                    st.write(f"**Customer:** {project[2]}")
                    st.write(f"**Category:** {project[3]}")
                    st.write(f"**PIC:** {project[4]}")
                    st.write(f"**Period:** {project[6]} to {project[7]}")
                    
                    progress = {
                        "Not Started": 0,
                        "On Going": 50,
                        "Waiting BA": 80,
                        "Completed": 100
                    }.get(status, 0)
                    
                    st.progress(progress)
                    st.write(f"**PO:** {project[8] or 'N/A'}")
                    st.write(f"**BAST:** {project[9] or 'N/A'}")

# Manage Files
def manage_files():
    st.subheader("📂 Manage Project Files", divider="blue")
    
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
    
    required_files = [
        "Form Request",
        "Form Tim Project",
        "Form Time Schedule",
        "SPK",
        "BAST",
        "Report"
    ]
    
    st.markdown("### 📤 Upload Documents")
    selected_category = st.selectbox("Document Type", required_files)
    uploaded_file = st.file_uploader(
        f"Choose {selected_category} file",
        type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'],
        key=f"uploader_{selected_project_id}_{selected_category}"
    )
    
    if st.button("⬆️ Upload") and uploaded_file:
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_name FROM project_files 
                WHERE project_id=? AND file_category=?
            """, (selected_project_id, selected_category))
            existing_file = cursor.fetchone()
            
            directory = f"files/project_{selected_project_id}/"
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, uploaded_file.name)
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if existing_file:
                cursor.execute("""
                    UPDATE project_files 
                    SET file_name=?, file_path=? 
                    WHERE project_id=? AND file_category=?
                """, (uploaded_file.name, filepath, selected_project_id, selected_category))
                st.success(f"♻️ {selected_category} updated successfully!")
            else:
                cursor.execute("""
                    INSERT INTO project_files (project_id, file_name, file_path, file_category) 
                    VALUES (?, ?, ?, ?)
                """, (selected_project_id, uploaded_file.name, filepath, selected_category))
                st.success(f"✅ {selected_category} uploaded successfully!")
    
    st.markdown("### 📂 Project Documents")
    with sqlite3.connect('project_management.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_name, file_path, file_category 
            FROM project_files 
            WHERE project_id=?
        """, (selected_project_id,))
        files = cursor.fetchall()
    
    if files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                if os.path.exists(file[2]):
                    zipf.write(file[2], arcname=file[1])
        
        st.download_button(
            label="⬇️ Download All Files (ZIP)",
            data=zip_buffer,
            file_name=f"{selected_project_name.replace(' ', '_')}_files.zip",
            mime="application/zip"
        )
        
        for file in files:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                st.markdown(f"**{file[3]}**: `{file[1]}`")
            with cols[1]:
                if os.path.exists(file[2]):
                    st.download_button(
                        label="Download",
                        data=open(file[2], "rb").read(),
                        file_name=file[1],
                        mime="application/octet-stream",
                        key=f"dl_{file[0]}"
                    )
                else:
                    st.warning("Missing")
            with cols[2]:
                if st.button("🗑️", key=f"del_{file[0]}"):
                    try:
                        os.remove(file[2])
                        with sqlite3.connect('project_management.db') as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                DELETE FROM project_files 
                                WHERE id=?
                            """, (file[0],))
                            conn.commit()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {e}")
    else:
        st.info("No documents uploaded yet")

# Initialize database
init_db()

# Main App
if 'show_edit_form' not in st.session_state:
    st.session_state['show_edit_form'] = False

if st.session_state['show_edit_form']:
    edit_project(st.session_state['edit_project_id'])
else:
    tabs = st.tabs(["📋 Board", "📅 Timeline", "➕ Add Project", "✏️ Edit Project", "🗑️ Delete Project", "📂 Manage Files"])

    with tabs[0]:
        view_projects_kanban()

    with tabs[1]:
        view_timeline()

    with tabs[2]:
        add_project()

    with tabs[3]:  # Edit Project tab
        st.subheader("✏️ Edit Project")
        projects = get_all_projects()
        if projects:
            project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
            selected_project = st.selectbox("Select Project to Edit", list(project_options.keys()))
            edit_project(project_options[selected_project])
        else:
            st.info("No projects available to edit")

    with tabs[4]:
        st.subheader("🗑️ Delete Project")
        projects = get_all_projects()
        if projects:
            project_options = {f"{p[1]} - {p[2]}": p[0] for p in projects}
            selected_project = st.selectbox("Select Project to Delete", list(project_options.keys()))
            delete_project(project_options[selected_project])
        else:
            st.info("No projects available to delete")

    with tabs[5]:
        manage_files()
