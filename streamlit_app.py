import os

import streamlit as st
from groq import Groq

from clarix_core import build_system_prompt, run_agent


# ---------------- SETTINGS ----------------

# Model name lives here (and in secrets) so the next deprecation is a one-line change.
MODEL = st.secrets.get("GROQ_MODEL", "openai/gpt-oss-120b")

# While stock levels, lead times and bulk prices in products.csv are sample data, keep True.
# Set to False once products.csv holds real ShaNeal data.
DEMO_DATA = True

MAX_HISTORY = 20


# ---------------- PAGE SETUP ----------------

st.set_page_config(
    page_title="CLARIX — ShaNeal Distributors",
    page_icon="🟢",
    layout="centered"
)

st.title("CLARIX — ShaNeal Distributors AI Assistant")
st.caption("Ask about products, request a quote, or get support.")

if DEMO_DATA:
    st.info("Demo mode: stock levels, lead times and bulk discounts shown here are sample data. "
            "Please confirm availability with ShaNeal before ordering.")

SYSTEM_PROMPT = build_system_prompt(DEMO_DATA)


# ---------------- API CONNECTION ----------------

client = Groq(api_key=st.secrets["GROQ_API_KEY"])


# ---------------- CHAT FUNCTION ----------------

def ask_clarix():
    history = st.session_state.messages[-MAX_HISTORY:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]

    reply, pdf_file = run_agent(client, MODEL, messages)

    if pdf_file:
        st.session_state.latest_quote = pdf_file
    return reply


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "latest_quote" not in st.session_state:
    st.session_state.latest_quote = None


# ---------------- UI ----------------

with st.sidebar:
    st.header("Quick Actions")

    quick_questions = [
        "What stationery products do you stock?",
        "Can I get a quote for 10 Butterfly A4 Paper reams?",
        "Calculate VAT on R5,500.",
        "I need PPE for 20 staff members.",
        "Help me set up a new office for 10 staff.",
        "How can I contact ShaNeal Distributors?"
    ]

    for question in quick_questions:
        if st.button(question):
            st.session_state.pending_question = question

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type your message here...")

if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("CLARIX is thinking..."):
            reply = ask_clarix()
            st.markdown(reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

if st.session_state.latest_quote and os.path.exists(st.session_state.latest_quote):
    with open(st.session_state.latest_quote, "rb") as file:
        st.download_button(
            label="📄 Download Latest Quote",
            data=file,
            file_name=os.path.basename(st.session_state.latest_quote),
            mime="application/pdf"
        )

st.markdown("---")
st.caption("CLARIX AI · Powered and Developed by Nikhil Dante Mooloo · ShaNeal Distributors · Pretoria")
