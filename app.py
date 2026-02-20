import streamlit as st
import google.generativeai as genai
import json
import random
from datetime import datetime, timedelta

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="AI Medical Assistant", page_icon="🩺")

# ------------------ DISCLAIMER ------------------
st.warning(
    """
⚠️ This AI assistant provides general medical guidance only.
It does NOT provide medical diagnoses and does NOT replace professional medical consultation.
If you are experiencing a medical emergency, please seek immediate medical attention.
"""
)

# ------------------ LOAD API KEY ------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# ------------------ LOAD DOCTORS ------------------
with open("doctors.json", "r") as f:
    doctors = json.load(f)

# ------------------ SESSION STATE ------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------ TITLE ------------------
st.title("🩺 AI Medical Assistant")

# ------------------ DISPLAY CHAT HISTORY ------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ------------------ USER INPUT ------------------
user_input = st.chat_input("Describe your symptoms or medical concern...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    # ------------------ PROMPT ------------------
    prompt = f"""
    You are a professional AI medical assistant.

    Your tasks:
    1. Provide general medical guidance.
    2. Assess the risk level as one of: LOW, MEDIUM, or HIGH.
    3. If HIGH risk, strongly recommend urgent medical care.
    4. Do NOT provide a definitive diagnosis.
    5. Do NOT prescribe specific medications.
    6. Provide basic self-care advice when appropriate.

    Respond using this format:

    Guidance:
    <general explanation and advice>

    Risk Level:
    <LOW / MEDIUM / HIGH>

    When to Seek Care:
    <clear instructions>

    Patient description:
    {user_input}
    """

    response = model.generate_content(prompt)
    assistant_response = response.text

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_response}
    )

    with st.chat_message("assistant"):
        st.write(assistant_response)

        # ------------------ APPOINTMENT SECTION ------------------
        st.markdown("### 📅 Schedule a Consultation")

        if st.button("Generate Available Appointment"):

            selected_doctor = random.choice(doctors)

            random_days = random.randint(0, 3)
            random_hour = random.randint(9, 18)

            appointment_date = datetime.now() + timedelta(days=random_days)
            appointment_time = appointment_date.replace(hour=random_hour, minute=0)

            confirmation_message = f"""
            ✅ Appointment Successfully Generated

            Doctor: {selected_doctor['name']}
            Specialty: {selected_doctor['specialty']}
            Mode: {selected_doctor['mode']}
            Date: {appointment_time.strftime('%B %d, %Y')}
            Time: {appointment_time.strftime('%I:%M %p')}

            A confirmation email has been sent (simulated).
            """

            st.success(confirmation_message)
