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
                st.rerun()
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
            st.rerun()
    else:
        st.error("⚠️ Project not found")

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

def view_projects_kanban():
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
                            st.rerun()
                    
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

def manage_files(project_id=None):
    st.subheader("📂 Manage Project Files", divider="blue")
    
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
    
    tab1, tab2 = st.tabs(["📋 Required Documents", "📂 Additional Files"])
    
    with tab1:
        required_files = [
            "Form Request",
            "Form Tim Project",
            "Form Time Schedule",
            "SPK",
            "BAST",
            "Report"
        ]
        
        st.markdown("### 📤 Upload Required Documents")
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
                    with sqlite3.connect('project_management.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT file_name FROM project_files 
                            WHERE project_id=? AND file_category=?
                        """, (selected_project_id, selected_category))
                        existing_file = cursor.fetchone()
                        
                        directory = f"files/project_{selected_project_id}/required/"
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
                    st.rerun()
        
        st.markdown("### 📋 Required Documents Status")
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_category, file_name 
                FROM project_files 
                WHERE project_id=? AND file_category IN (
                    'Form Request', 'Form Tim Project', 
                    'Form Time Schedule', 'SPK', 'BAST', 'Report'
                )
            """, (selected_project_id,))
            existing_files = {row[0]: row[1] for row in cursor.fetchall()}
        
        for doc in required_files:
            status = "✅" if doc in existing_files else "❌"
            cols = st.columns([1, 4, 2])
            with cols[0]:
                st.markdown(status)
            with cols[1]:
                st.markdown(f"**{doc}**")
            with cols[2]:
                if doc in existing_files:
                    file_path = f"files/project_{selected_project_id}/required/{existing_files[doc]}"
                    if os.path.exists(file_path):
                        st.download_button(
                            "Download",
                            data=open(file_path, "rb").read(),
                            file_name=existing_files[doc],
                            key=f"dl_req_{doc}_{selected_project_id}"
                        )
                    else:
                        st.warning("File missing")
    
    with tab2:
        st.markdown("### 🆕 Upload Additional Files")
        
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
                    st.rerun()
        
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
            for file in additional_files:
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
                            key=f"dl_add_{file[0]}"
                        )
                    else:
                        st.warning("Missing")
                
                with cols[2]:
                    if st.button("🗑️", key=f"del_add_{file[0]}"):
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
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {str(e)}")
        else:
            st.info("No additional files uploaded yet")

    st.markdown("---")
    st.markdown("### 🗂 Download All Project Files")
    
    if st.button("⬇️ Download All Files as ZIP"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            required_dir = f"files/project_{selected_project_id}/required/"
            if os.path.exists(required_dir):
                for file in os.listdir(required_dir):
                    file_path = os.path.join(required_dir, file)
                    if os.path.isfile(file_path):
                        zipf.write(file_path, arcname=f"Required Documents/{file}")
            
            additional_dir = f"files/project_{selected_project_id}/additional/"
            if os.path.exists(additional_dir):
                for file in os.listdir(additional_dir):
                    file_path = os.path.join(additional_dir, file)
                    if os.path.isfile(file_path):
                        zipf.write(file_path, arcname=f"Additional Files/{file}")
        
        if zip_buffer.tell() > 0:
            st.download_button(
                label="💾 Download ZIP Now",
                data=zip_buffer,
                file_name=f"{selected_project_name.replace(' ', '_')}_ALL_FILES.zip",
                mime="application/zip"
            )
        else:
            st.warning("No files available to download")
            
 with tab_preview:
        st.markdown(f"### 📑 File Preview: {selected_project_name}")
        
        # Filter file
        col1, col2 = st.columns(2)
        with col1:
            file_type = st.selectbox(
                "Filter File Type",
                ["All", "Required Documents", "Additional Files"],
                key="file_type_filter"
            )
        with col2:
            search_query = st.text_input("🔍 Search by filename")
        
        # Ambil file dari database
        with sqlite3.connect('project_management.db') as conn:
            cursor = conn.cursor()
            query = """
                SELECT file_name, file_path, file_category 
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
        
        # Tampilkan file
        if not files:
            st.info("No files found")
        else:
            for file in files:
                file_name, file_path, file_category = file
                file_ext = os.path.splitext(file_name)[1].lower()
                
                with st.expander(f"📄 {file_name} ({file_category})"):
                    # Kolom untuk tombol aksi
                    col1, col2, col3 = st.columns([4, 1, 1])
                    
                    with col1:
                        st.markdown(f"**Type:** {file_category}")
                        st.markdown(f"**Size:** {os.path.getsize(file_path) / 1024:.2f} KB")
                    
                    with col2:
                        # Tombol preview
                        if file_ext in PREVIEW_SUPPORTED:
                            if st.button("👁️ Preview", key=f"preview_{file_path}"):
                                st.session_state['preview_file'] = file_path
                    
                    with col3:
                        # Tombol download
                        with open(file_path, "rb") as f:
                            st.download_button(
                                "⬇️ Download",
                                data=f,
                                file_name=file_name,
                                key=f"dl_{file_path}"
                            )
                    
                    # Preview file (jika dipilih)
                    if st.session_state.get('preview_file') == file_path:
                        st.markdown("---")
                        st.markdown("### File Preview")
                        
                        if file_ext == '.pdf':
                            # Preview PDF (menggunakan komponen Streamlit)
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
                        
                        else:
                            st.warning("Preview not available for this file type")


# Initialize database
init_db()

# Initialize session states
if 'show_edit_form' not in st.session_state:
    st.session_state['show_edit_form'] = False
if 'edit_project_id' not in st.session_state:
    st.session_state['edit_project_id'] = None
if 'view_files_project' not in st.session_state:
    st.session_state.view_files_project = None

# Main App Logic
if st.session_state['show_edit_form']:
    edit_project(st.session_state['edit_project_id'])
elif st.session_state.view_files_project:
    project_id = st.session_state.view_files_project
    project_details = get_project_details(project_id)
    
    if project_details:
        st.subheader(f"📂 Files for: {project_details[1]}")
        
        if st.button("← Back to Board"):
            st.session_state.view_files_project = None
            st.rerun()
        
        manage_files(project_id=project_id)
    else:
        st.error("Project not found")
        st.session_state.view_files_project = None
else:
    tabs = st.tabs(["📋 Board", "📅 Timeline", "➕ Add Project", "✏️ Edit Project", "🗑️ Delete Project", "📂 Manage Files"])

    with tabs[0]:
        view_projects_kanban()

    with tabs[1]:
        view_timeline()

    with tabs[2]:
        add_project()

    with tabs[3]:
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
