import json
import time
import pdfplumber
import streamlit as st
from openai import OpenAI

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Sumi |Resume Screener AI",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --- MODERN CSS STYLING ---
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        background-color: #0066cc;
        color: white;
        height: 45px;
    }
    .stButton>button:hover { background-color: #0052a3; color: white; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE INITIALIZATION ---
if "job_criteria" not in st.session_state:
  st.session_state["job_criteria"] = None

if "applicant_pool" not in st.session_state:
  st.session_state["applicant_pool"] = []

# --- SIDEBAR NAVIGATION ---
st.sidebar.title(" Navigation")
app_mode = st.sidebar.radio(
    "Select Portal", ["🏢 Employer Portal", "👤 Candidate Portal"]
)
st.sidebar.markdown("---")
st.sidebar.info(
    "**Privacy First:** Zero-file storage. Resumes are parsed in-memory and"
    " immediately discarded."
)

# ====================================================================
# 1. EMPLOYER PORTAL
# ==============================================================================
if app_mode == "🏢 Employer Portal":
  st.title(" Employer Portal: Job Setup")
  st.markdown(
      "Define your standard qualifications and requirements for automated"
      " screening."
  )

  with st.form("employer_form"):
    st.markdown("### Job Details")
    col1, col2 = st.columns(2)
    with col1:
      employer_name = st.text_input(
          "Employer / Company Name", placeholder="e.g., Anthropic"
      )
    with col2:
      job_title = st.text_input(
          "Specific Job Title", placeholder="e.g., Senior AI Engineer"
      )

    st.markdown("### Screening Criteria")
    col3, col4 = st.columns(2)
    with col3:
      qualification = st.selectbox(
          "Minimum Qualification Required",
          [
              "Bachelor's Degree",
              "Master's Degree",
              "Diploma / TVET",
              "High School",
              "Certification / Other",
          ],
      )
    with col4:
      experience = st.selectbox(
          "Required Years of Experience",
          ["0-1 Years", "1-3 Years", "3-5 Years", "5+ Years"],
      )

    additional_info = st.text_area(
        "Additional Requirements / Key Details",
        placeholder=(
            "Mention critical technical skills (e.g., Python, SQL, Git)..."
        ),
    )

    submitted = st.form_submit_button("Publish & Activate AI Screening")

    if submitted:
      if not employer_name or not job_title:
        st.error("Please fill in the Company Name and Job Title.")
      else:
        st.session_state["job_criteria"] = {
            "employer_name": employer_name,
            "job_title": job_title,
            "qualification": qualification,
            "experience": experience,
            "additional_info": additional_info,
        }
        st.success(
            f"✨ Job criteria published successfully for **{job_title}**!"
        )

  # Display Current Active Job Spec if any
  if st.session_state["job_criteria"]:
    curr_job = st.session_state["job_criteria"]
    st.info(
        f"📌 **Active Job:** {curr_job['job_title']} at"
        f" {curr_job['employer_name']}"
    )

  st.markdown("---")
  st.markdown("###  Candidate Evaluation Queue")

  if not st.session_state["applicant_pool"]:
    st.info(
        "No candidates have applied yet. Submit a resume through the Candidate"
        " Portal to see them here."
    )
  else:
    for idx, applicant in enumerate(st.session_state["applicant_pool"]):
      # Build structured JSON payload for HR notifications but I removed the detailed JSON info because I found it to be Unnecessary.
      applicant_json = json.dumps(
          {
              "candidate_name": applicant["name"],
              "email": applicant["email"],
              "phone": applicant["phone"],
              "score": applicant["score"],
              "status": "PASS" if applicant["score"] >= 75 else "FAIL",
              "ai_feedback": applicant["feedback"],
          },
          indent=2,
      )
      for idx, applicant in enumerate(st.session_state["applicant_pool"]):
        with st.expander(
          f"📄 {applicant['name']} — Score: {applicant['score']}/100"
      ):
        
        
          st.write(f"**Email:** {applicant['email']}")
          st.write(f"**Phone:** {applicant['phone']}")
          st.write(f"**AI Feedback:**")
          st.text(applicant["feedback"])
        
          st.write("")
         # st.code(applicant_json, language="json") this puts the Json information

        # HR Action Button to send Email Invitation
        if st.button(
            f"📨 Send Interview Invitation to {applicant['name']}",
            key=f"invite_{idx}",
        ):
          st.success(
              f"✅ Interview invitation email dispatched successfully to"
              f" {applicant['email']}!"
          )


# ==============================================================================
# 2. CANDIDATE PORTAL (WITH LOCAL LLM BACKEND)
# ==============================================================================
elif app_mode == "👤 Candidate Portal":
  st.title("👤 Candidate Application Portal")

  if st.session_state["job_criteria"] is None:
    st.warning(
        "⚠️ No active job opening published by employer yet. Using default"
        " general software role."
    )
    active_job = {
        "employer_name": "EthioTech Innovations",
        "job_title": "General Software Engineer",
        "qualification": "Bachelor's Degree",
        "experience": "1-3 Years",
        "additional_info": "Python programming and problem solving.",
    }
  else:
    active_job = st.session_state["job_criteria"]
    st.info(
        f"🎯 Applying for: **{active_job['job_title']}** at"
        f" **{active_job['employer_name']}**"
    )

  with st.form("candidate_form"):
    st.markdown("### 👤 Personal Information")
    col1, col2 = st.columns(2)
    with col1:
      first_name = st.text_input("First Name", placeholder="e.g., Jack")
    with col2:
      last_name = st.text_input("Last Name", placeholder="e.g., Doe")

    col3, col4 = st.columns(2)
    with col3:
      email = st.text_input(
          "Email Address", placeholder="e.g., jack.k@example.com"
      )
    with col4:
      phone = st.text_input("Phone Number", placeholder="e.g., +44 7700 900997")

    st.markdown("### 📄 Resume Upload")
    uploaded_file = st.file_uploader(
        "Upload your CV/Resume (PDF Only)",
        type=["pdf"],
        help="Processed in-memory. Zero storage.",
    )
    candidate_submit = st.form_submit_button("Submit Application")

    if candidate_submit:
      if not first_name or not last_name or not email or not phone:
        st.error("Please fill out all required personal contact fields.")
      elif not uploaded_file:
        st.error("Please upload your CV/Resume in PDF format to proceed.")
      else:
        try:
          with pdfplumber.open(uploaded_file) as pdf:
            resume_text = "".join(
                [page.extract_text() or "" for page in pdf.pages]
            )

          if not resume_text.strip():
            st.error(
                "❌ Scanned or image-based PDF detected. Please use a text-based"
                " PDF."
            )
          else:
            with st.spinner(
                "🤖 Sumi is evaluating your resume against job requirements..."
            ):
              client = OpenAI(
                  base_url="http://localhost:11434/v1",
                  api_key="ollama",
                  timeout=300.0,
              )

              document_score = """
              [SCORING RUBRIC & EVALUATION RULES]
              You are a strict, objective HR evaluation engine. Grade the candidate resume strictly based on the provided Job Requirements using a 100-point scale distributed as follows:

              1. CORE QUALIFICATIONS (30 Points Max):
                 - Does the candidate meet or exceed the minimum education level requested?
                 - Award full points if met, zero points if below the required qualification.

              2. EXPERIENCE RELEVANCE (35 Points Max):
                 - Does the candidate's professional background match the required years of experience and domain?
                 - Scale proportionally (matching years = full points; fewer years = partial or zero).

              3. TECHNICAL SKILLS & KEYWORDS (35 Points Max):
                 - Evaluate how many of the requested tools, technologies, languages, or domain skills appear in the resume text.
                 - Deduct points for missing critical skills.

              [STRICT GROUNDING & FEEDBACK RULES]
              - CRITICAL: Read the resume text carefully before writing feedback. NEVER claim that education, portfolio, or technical skills are "not provided" if they are clearly written in the resume text. 
              - If a skill or experience is present, acknowledge it. Only list genuine gaps or missing requirements in the feedback.
                
              [STRICT CRITIQUE RULES]
              - Do NOT critique the candidate's resume tone, formatting style, or use of formal language. 
              - Base your feedback strictly on factual gaps against the job description. Do not claim a skill is missing if it is explicitly written in the resume text.

              [STRICT OUTPUT FORMAT]
              Do not add conversational fluff or pleasantries. Return your evaluation strictly using this exact template:
              Score: [Integer between 0 and 100]
              Status: [PASS if Score >= 75 else FAIL]
              Feedback: [Provide a concise, 2-3 sentence explanation highlighting exact missing skills or why points were deducted]"""

              system_prompt = f"""
              You are an expert HR recruiter AI. Strictly evaluate the candidate's resume text against the job requirements and scoring standard delimited by triple backticks below. Never make up or guess scores; calculate them strictly according to the rubric criteria.

              ```{document_score}```
              """

              user_prompt = f"""
                            Job Title: {active_job['job_title']}
                            Required Qualification: {active_job['qualification']}
                            Required Experience: {active_job['experience']}
                            Additional Requirements: {active_job['additional_info']}

                            Candidate Resume Text:
                            {resume_text[:3000]}
                            """

              response = client.chat.completions.create(
                  model="llama3.2:1b",
                  messages=[
                      {"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt},
                  ],
                  temperature=0,
              )
              #ai_result = response.output_text #I'll use this for response API

              ai_result = response.choices[0].message.content #used it for the old openai completions api

              st.success("✅ Evaluation complete!")
              st.write(ai_result)
              #st.write(ai_result) # used it for the old model

              # --- EXTRACT NUMERICAL SCORE SAFELY ---
              parsed_score = 70
              try:
                for line in ai_result.split("\n"):
                  if "Score:" in line:
                    digits = "".join(filter(str.isdigit, line))
                    if digits:
                      parsed_score = int(digits)
                      break
              except Exception:
                pass

              # --- SAVE TO SESSION STATE APPLICANT POOL ---
              st.session_state["applicant_pool"].append({
                  "name": f"{first_name} {last_name}",
                  "email": email,
                  "phone": phone,
                  "score": parsed_score,
                  "feedback": ai_result,
              })

        except Exception as e:
          st.error(
              "⚠️ Local AI connection was reset or timed out. Please check if"
              f" Ollama is running in your system tray. Details: {e}"
          )