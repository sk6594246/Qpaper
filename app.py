import os
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
    api_key_input = st.text_input("Enter Gemini API Key", type="password")
    
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input
        st.success("API Key saved for session!")
    
    st.divider()
    st.markdown("### 🏫 School Info")
    school_name = st.text_input("School Name", "Global Public School")
    class_name = st.text_input("Class / Grade", "Grade 10 - Science")

# Ensure API key is configured
api_key = st.session_state.get("gemini_api_key")
if not api_key:
    st.warning("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")
    st.stop()

# Initialize the official Google GenAI client
client = genai.Client(api_key=api_key)

# --- MAIN INPUT SECTION ---
st.subheader("📁 Upload Materials & Reference Artifact")

col1, col2 = st.columns(2)
with col1:
    primary_file = st.file_uploader(
        "Source Snap / Document (Image/PDF)", 
        type=["png", "jpg", "jpeg", "pdf"]
    )
with col2:
    reference_artifact = st.file_uploader(
        "Reference Paper Artifact (Optional)", 
        type=["png", "jpg", "jpeg", "pdf"]
    )

instructions = st.text_area(
    "Custom Instructions (Optional)", 
    placeholder="e.g., Include 5 MCQs, 3 short answers, and 2 long descriptive questions."
)

# --- PDF GENERATOR HELPER CLASS ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, school_name, 0, 1, 'C')
        self.set_font('Arial', '', 11)
        self.cell(0, 6, f"Class: {class_name}", 0, 1, 'C')
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
    # Multi_cell handles text wrapping safely
    pdf.multi_cell(0, 6, content)
    return pdf.output(dest='S').encode('latin1')

# --- GENERATION LOGIC ---
if st.button("🚀 Generate Question Paper & Answer Sheet", type="primary"):
    if not primary_file:
        st.error("Please upload a source image or PDF document.")
    else:
        with st.spinner("Processing documents with Gemini and applying document grounding..."):
            try:
                # Upload files using GenAI Files API
                uploaded_source = client.files.upload(file=primary_file)
                contents_payload = [uploaded_source]
                
                if reference_artifact:
                    uploaded_ref = client.files.upload(file=reference_artifact)
                    contents_payload.append(uploaded_ref)

                prompt_text = f"""
                You are an expert academic examiner. 
                Using strictly and exclusively the attached source document(s), generate two distinct sections:
                1. QUESTION PAPER: Formulate well-structured examination questions based ONLY on the provided source text/images. Follow any formatting cues if a reference artifact was provided.
                2. ANSWER SHEET: Provide clear, accurate model answers for every question generated in the question paper.
                
                Additional instructions from user: {instructions}
                
                Format your output clearly with markers:
                === QUESTION PAPER ===
                [Insert Question Paper Content Here]
                
                === ANSWER SHEET ===
                [Insert Answer Sheet Content Here]
                """
                contents_payload.append(prompt_text)

                # Call Gemini 2.5 Flash model
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
                    qp_bytes = create_pdf_bytes(f"Question Paper - {class_name}", qp_content)
                    st.download_button("Download Question Paper PDF", qp_bytes, file_name="Question_Paper.pdf", mime="application/pdf")

                with tab2:
                    st.markdown(ans_content)
                    ans_bytes = create_pdf_bytes(f"Answer Sheet - {class_name}", ans_content)
                    st.download_button("Download Answer Sheet PDF", ans_bytes, file_name="Answer_Sheet.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                === ANSWER SHEET ===
                [Insert Answer Sheet Content Here]
                """
                contents_payload.append(prompt_text)

                # Call Gemini 2.5 Flash model
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
                    qp_bytes = create_pdf_bytes(f"Question Paper - {class_name}", qp_content)
                    st.download_button("Download Question Paper PDF", qp_bytes, file_name="Question_Paper.pdf", mime="application/pdf")

                with tab2:
                    st.markdown(ans_content)
                    ans_bytes = create_pdf_bytes(f"Answer Sheet - {class_name}", ans_content)
                    st.download_button("Download Answer Sheet PDF", ans_bytes, file_name="Answer_Sheet.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"An error occurred: {e}")
              
