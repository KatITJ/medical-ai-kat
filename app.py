import streamlit as st
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.oauth2 import service_account
import json
from datetime import datetime

# ------------------ CONFIG ------------------
PROJECT_ID = "neurodocsdomain"
LOCATION = "us-west1"

# 🔐 USE SERVICE ACCOUNT FROM STREAMLIT SECRETS
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp"]
)

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    credentials=credentials,
)

model = GenerativeModel("gemini-2.5-flash-lite")

st.set_page_config(page_title="AI Medical Assistant", page_icon="🩺")

# ------------------ DISCLAIMER ------------------
st.warning(
    """
⚠️ This AI assistant provides general medical guidance only.
It does NOT provide medical diagnoses and does NOT replace professional medical consultation.
If you are experiencing a medical emergency, please seek immediate medical attention.
"""
)

# ------------------ LOAD DOCTORS ------------------
with open("doctors.json", "r") as f:
    doctors = json.load(f)

# ------------------ SESSION STATE ------------------
if "state" not in st.session_state:
    st.session_state.state = "symptoms"

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "recommended_specialty" not in st.session_state:
    st.session_state.recommended_specialty = None

if "risk_level" not in st.session_state:
    st.session_state.risk_level = None

# ------------------ UI ------------------
st.title("🩺 AI Medical Assistant")

# ==========================================================
# STATE 1 — SYMPTOMS INPUT
# ==========================================================

if st.session_state.state == "symptoms":

    st.markdown("### Describe your symptoms")

    user_input = st.text_area(
        label="",
        height=180,
        placeholder="Example: I have had a fever and sore throat for two days...",
    )

    if st.button("Analyze & Find Specialist"):

        if not user_input:
            st.warning("Please describe your symptoms.")
            st.stop()

        prompt = f"""
        You are a professional AI medical assistant.

        Tasks:
        1. Provide general medical guidance.
        2. Assess risk level: LOW, MEDIUM, or HIGH.
        3. Suggest medical specialty.
        4. If HIGH risk, recommend urgent care.
        5. Do NOT diagnose.
        6. Do NOT prescribe medications.

        Format strictly:

        Guidance:
        <text>

        Risk Level:
        <LOW / MEDIUM / HIGH>

        Recommended Specialty:
        <General Medicine / Internal Medicine / Infectious Diseases>

        When to Seek Care:
        <text>

        Patient description:
        {user_input}
        """

        with st.spinner("Analyzing symptoms..."):
            try:
                response = model.generate_content(prompt)
                result_text = response.candidates[0].content.parts[0].text

                st.session_state.analysis_result = result_text

                # Parse risk
                if "Risk Level:" in result_text:
                    st.session_state.risk_level = (
                        result_text.split("Risk Level:")[1].split("\n")[0].strip()
                    )

                # Parse specialty
                if "Recommended Specialty:" in result_text:
                    st.session_state.recommended_specialty = (
                        result_text.split("Recommended Specialty:")[1]
                        .split("\n")[0]
                        .strip()
                    )

                st.session_state.state = "analysis"
                st.rerun()

            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

# ==========================================================
# STATE 2 — SHOW ANALYSIS
# ==========================================================

elif st.session_state.state == "analysis":

    st.markdown("---")
    st.markdown(st.session_state.analysis_result)

    if st.session_state.risk_level == "HIGH":
        st.error("⚠️ High risk detected. Immediate medical attention is recommended.")

    if st.button("Proceed to Schedule Appointment"):
        st.session_state.state = "booking"
        st.rerun()

# ==========================================================
# STATE 3 — BOOKING FORM
# ==========================================================

elif st.session_state.state == "booking":

    st.markdown("## 🧾 Patient Information")

    # Filter doctors by specialty
    filtered_doctors = [
        d for d in doctors if d["specialty"] == st.session_state.recommended_specialty
    ]

    if not filtered_doctors:
        filtered_doctors = doctors

    with st.form("appointment_form"):

        full_name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")

        selected_doctor = st.selectbox(
            "Select Doctor",
            filtered_doctors,
            format_func=lambda x: f"{x['name']} ({x['mode']})",
        )

        available_times = selected_doctor["availability"]

        # If HIGH risk → only today slots
        if st.session_state.risk_level == "HIGH":
            today_str = datetime.now().strftime("%Y-%m-%d")
            available_times = [t for t in available_times if today_str in t]

        selected_time = st.selectbox(
            "Available Appointment Times",
            available_times if available_times else ["No immediate slots available"],
        )

        submitted = st.form_submit_button(
            "Confirm Appointment", use_container_width=True
        )

        if submitted:

            if not full_name or not phone or not email:
                st.warning("Please complete all patient information fields.")
            elif "No immediate slots" in selected_time:
                st.error("No available slots. Please contact emergency services.")
            else:
                st.session_state.confirmation_data = {
                    "name": full_name,
                    "age": age,
                    "phone": phone,
                    "email": email,
                    "doctor": selected_doctor,
                    "time": selected_time,
                }
                st.session_state.state = "confirmed"
                st.rerun()

# ==========================================================
# STATE 4 — CONFIRMATION
# ==========================================================

elif st.session_state.state == "confirmed":

    data = st.session_state.confirmation_data

    st.success(
        f"""
✅ Appointment Confirmed

Patient: {data['name']}  
Age: {data['age']}  
Phone: {data['phone']}  
Email: {data['email']}  

Doctor: {data['doctor']['name']}  
Specialty: {data['doctor']['specialty']}  
Mode: {data['doctor']['mode']}  
Date & Time: {data['time']}

A confirmation email has been sent (simulated).
"""
    )

    if st.button("Start New Consultation"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.state = "symptoms"
        st.rerun()
