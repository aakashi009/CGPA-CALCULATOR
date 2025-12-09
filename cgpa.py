import streamlit as st
import pdfplumber
import re

# --- CONFIGURATION ---
# Updated grading scale with D- included
GRADE_POINTS = {
    "A": 10,
    "A-": 9,
    "B": 8,
    "B-": 7,
    "C": 6,
    "C-": 5,
    "D": 4,
    "D-": 3,
    "E": 2,
    "F": 0
}

def extract_subjects_from_pdf(uploaded_file):
    """
    Robust text-based extraction.
    Scans for lines containing a Course Code (e.g., MEM601) and Credits (e.g., 3.00).
    """
    subjects = []
    
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                full_text += text + "\n"
    
    lines = full_text.split('\n')
    
    # Regex to find Code, Subject Name, and Credits
    pattern = re.compile(r'([A-Z]{3}\d{3})\s+(.+?)\s+(\d{1,2}\.\d{2})')

    for line in lines:
        match = pattern.search(line)
        if match:
            code = match.group(1).strip()
            name = match.group(2).strip()
            credit_str = match.group(3).strip()
            
            if "Course Code" in code or "Credits" in name:
                continue

            try:
                credit = float(credit_str)
                subjects.append({"Code": code, "Subject": name, "Credit": credit})
            except ValueError:
                continue

    return subjects

# --- APP UI ---
st.set_page_config(page_title="Smart CGPA Calculator", layout="centered")

st.title("🎓 Semester CGPA Predictor")
st.write("Upload your registration report (PDF), input your expected grades, and get your GPA range.")

# 1. File Upload
uploaded_file = st.file_uploader("Upload Registration Report (PDF)", type=["pdf"])

course_data = []

if uploaded_file is not None:
    course_data = extract_subjects_from_pdf(uploaded_file)
    
    if not course_data:
        st.error("Could not automatically detect subjects. Please ensure the PDF is a valid 'Student Registration Record' text PDF.")
    else:
        st.success(f"File Uploaded! Detected {len(course_data)} subjects.")
else:
    st.info("Please upload your PDF file to begin.")

# 2. Input Section
if course_data:
    st.markdown("---")
    st.subheader("📝 Enter Expected Grades")
    
    total_credits = 0.0
    user_inputs = []
    
    # Header Row
    c1, c2, c3 = st.columns([1.5, 3, 2])
    c1.markdown("**Code**")
    c2.markdown("**Subject**")
    c3.markdown("**Grade**")
    
    # Input Rows
    for i, item in enumerate(course_data):
        col1, col2, col3 = st.columns([1.5, 3, 2])
        
        with col1:
            st.code(item['Code'])
        with col2:
            st.write(f"{item['Subject']}")
            st.caption(f"Credits: {item['Credit']}")
            total_credits += item['Credit']
        with col3:
            grade = st.selectbox(
                "Grade", 
                options=list(GRADE_POINTS.keys()), 
                key=f"grade_{i}", 
                label_visibility="collapsed"
            )
            user_inputs.append({"credit": item['Credit'], "grade": grade})

    # 3. Calculation
    st.markdown("---")
    if st.button("Calculate SGPA", type="primary"):
        current_points = 0.0
        
        for entry in user_inputs:
            grade_point = GRADE_POINTS[entry['grade']]
            current_points += (grade_point * entry['credit'])
            
        if total_credits > 0:
            sgpa = current_points / total_credits
            sgpa = round(sgpa, 2)
            
            # --- UPDATED LOGIC ---
            # Range is: (Calculated CGPA - 0.5) TO (Calculated CGPA)
            lower_bound = round(sgpa - 0.5, 2)
            
            # Ensure lower bound doesn't go below 0
            if lower_bound < 0:
                lower_bound = 0.0

            st.balloons()
            
            # Displaying the range as requested
            st.success(f"Your expected CGPA is in between {lower_bound} to {sgpa}")
            
        else:
            st.error("Total credits cannot be zero.")