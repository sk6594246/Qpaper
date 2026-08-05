import os
import tempfile
import streamlit as st
from google import genai
from fpdf import FPDF

# Page configuration for mobile devices
st.set_page_config(
    page_title="School Question Paper Generator",
    page_icon="📝",
    layout="centered"
)

st.title("📚 AI Question Paper Generator")
st.write("Generate grounded Question Papers and Answer Sheets directly from your mobile device.")

# --- ONE-TIME CONFIGURATION PANEL ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Configuration
    if "gemini_api_key" not in st.session_state:
        st.session_state["gemini_api_key"] = ""
        
    api_key_input = st.text_input("Enter Gemini API Key", type="password", value=st.session_state["gemini_api_key"])
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input
        st.success("API Key saved for session!")
    
    st.divider()
    st.markdown("### 🏫 School & Class Info")
    
    # One-time / persistent school setup inputs saved to session state
    school_name = st.text_input("School Name", value=st.session_state.get("school_name", "Global Public School"))
    class_name = st.text_input("Class / Grade", value=st.session_state.get("class_name", "Grade 10 - Science"))
    
    st.session_state["school_name"] = school_name
    st.session_state["class_name"] = class_name
    
    st.divider()
    st.markdown("### 📋 Reference Artifact")
    st.info("Upload a reference question paper artifact once. It persists across generations until changed.")
    reference_artifact = st.file_uploader(
        "Reference Paper Artifact", 
        type=["png", "jpg", "jpeg", "pdf"],
        key="persistent_reference"
    )

# Ensure API key is configured
api_key = st.session_state.get("gemini_api_key")
if not api_key:
    st.warning("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")
    st.stop()

# Initialize the official Google GenAI client
client = genai.Client(api_key=api_key)

# --- MAIN INPUT SECTION ---
st.subheader("📁 Source Material")

primary_file = st.file_uploader(
    "Upload Source Snap or Document (Image/PDF)", 
    type=["png", "jpg", "jpeg", "pdf"],
    key="primary_source"
)

instructions = st.text_area(
    "Custom Instructions (Optional)", 
    placeholder="e.g., Include 5 MCQs, 3 short answers, and 2 long descriptive questions."
)

# --- PDF GENERATOR HELPER CLASS ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, st.session_state.get("school_name", "School"), 0, 1, 'C')
        self.set_font('Arial', '', 11)
        self.cell(0, 6, f"Class: {st.session_state.get('class_name', 'Class')}", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_bytes(title, content):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, title, 0, 1, 'L')
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, content)
    return pdf.output(dest='S').encode('latin1')

# Helper function to save uploaded file locally for Gemini API ingestion
def save_uploaded_file(uploaded_file):
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error handling file upload: {e}")
        return None

# --- GENERATION LOGIC ---
if st.button("🚀 Generate Question Paper & Answer Sheet", type="primary"):
    if not primary_file:
        st.error("Please upload a source image or PDF document.")
    else:
        with st.spinner("Processing documents with Gemini and applying document grounding..."):
            temp_source_path = None
            temp_ref_path = None
            try:
                # Save source file temporarily
                temp_source_path = save_uploaded_file(primary_file)
                uploaded_source = client.files.upload(file=temp_source_path)
                contents_payload = [uploaded_source]
                
                # Save reference artifact temporarily if provided in sidebar
                if reference_artifact:
                    temp_ref_path = save_uploaded_file(reference_artifact)
                    uploaded_ref = client.files.upload(file=temp_ref_path)
                    contents_payload.append(uploaded_ref)

                prompt_text = f"""
                You are an expert academic examiner representing {st.session_state['school_name']} for {st.session_state['class_name']}. 
                Using strictly and exclusively the attached source document(s), generate two distinct sections:
                1. QUESTION PAPER: Formulate well-structured examination questions based ONLY on the provided source text/images. Follow formatting cues from the reference artifact if provided.
                2. ANSWER SHEET: Provide clear, accurate model answers for every question generated in the question paper.
                
                Additional instructions from user: {instructions}
                
                Format your output clearly with markers:
                === QUESTION PAPER ===
                [Insert Question Paper Content Here]
                
                === ANSWER SHEET ===
                [Insert Answer Sheet Content Here]
                """
                contents_payload.append(prompt_text)

                # Call Gemini Flash model
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents_payload
                )
                
                full_text = response.text
                
                # Split output into Question Paper and Answer Sheet
                if "=== ANSWER SHEET ===" in full_text:
                    qp_part, ans_part = full_text.split("=== ANSWER SHEET ===", 1)
                    qp_content = qp_part.replace("=== QUESTION PAPER ===", "").strip()
                    ans_content = ans_part.strip()
                else:
                    qp_content = full_text
                    ans_content = "Answer sheet could not be automatically separated. Review raw output."

                st.success("Generation Complete!")

                tab1, tab2 = st.tabs(["📋 Question Paper", "✅ Answer Sheet"])
                
                with tab1:
                    st.markdown(qp_content)
                    qp_bytes = create_pdf_bytes(f"Question Paper - {st.session_state['class_name']}", qp_content)
                    st.download_button("Download Question Paper PDF", qp_bytes, file_name="Question_Paper.pdf", mime="application/pdf")

                with tab2:
                    st.markdown(ans_content)
                    ans_bytes = create_pdf_bytes(f"Answer Sheet - {st.session_state['class_name']}", ans_content)
                    st.download_button("Download Answer Sheet PDF", ans_bytes, file_name="Answer_Sheet.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                # Clean up temporary files
                if temp_source_path and os.path.exists(temp_source_path):
                    os.remove(temp_source_path)
                if temp_ref_path and os.path.exists(temp_ref_path):
                    os.remove(temp_ref_path)
