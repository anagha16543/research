import os
import tempfile

import streamlit as st
from groq import Groq
from streamlit_mic_recorder import mic_recorder

from chatbot import (
    initialize_chat,
    display_chat,
    ask_question,
    clear_chat
)

from rag import (
    build_vector_store
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="PragyanAI AI Assistant",
    page_icon="🤖",
    layout="wide"
)


# ==========================================================
# INITIALIZE CHAT
# ==========================================================

initialize_chat()


# ==========================================================
# GROQ CLIENT
# ==========================================================

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)


# ==========================================================
# SPEECH TO TEXT
# ==========================================================

def speech_to_text(audio_bytes):

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as temp:

        temp.write(audio_bytes)

        audio_path = temp.name

    try:

        with open(audio_path, "rb") as audio_file:

            transcript = client.audio.transcriptions.create(

                file=audio_file,

                model="whisper-large-v3-turbo",

                response_format="text"

            )

        return transcript.strip()

    finally:

        if os.path.exists(audio_path):

            os.remove(audio_path)


# ==========================================================
# TITLE
# ==========================================================

st.title("🤖 PragyanAI AI Assistant")

st.markdown(
"""
Ask anything about:

- 🎓 AI Programs
- 💰 Fees
- 📚 Curriculum
- 🏢 Placements
- 🎤 Voice Queries
- 📄 Uploaded PDFs
"""
)


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.header("Settings")

    persona = st.selectbox(

        "Choose Persona",

        [

            "PragyanAI Student Counselor",

            "PragyanAI Institutional / CoE Advisor",

            "PragyanAI Enterprise AI & Placement Lead"

        ]

    )

    st.divider()

    uploaded_files = st.file_uploader(

        "Upload PDF / Excel",

        type=["pdf", "xlsx", "xls"],

        accept_multiple_files=True

    )

    if uploaded_files:

        with st.spinner("Building Knowledge Base..."):

            build_vector_store(uploaded_files)

        st.success("Knowledge Base Ready")

    st.divider()

    if st.button("🗑 Clear Chat"):

        clear_chat()

        st.rerun()
# ==========================================================
# CHAT HISTORY
# ==========================================================

st.divider()

st.subheader("💬 Chat")

display_chat()


# ==========================================================
# VOICE INPUT
# ==========================================================

st.subheader("🎤 Speak")

voice = mic_recorder(
    start_prompt="🎙️ Start Recording",
    stop_prompt="⏹️ Stop Recording",
    just_once=False,
    use_container_width=True,
    key="voice_input"
)

speech_text = ""

if voice:

    try:

        audio_bytes = voice.get("bytes")

        if audio_bytes is None:
            audio_bytes = voice.get("audio")

        if audio_bytes:

            with st.spinner("Converting speech to text..."):

                speech_text = speech_to_text(audio_bytes)

            st.success("Speech recognized successfully!")

            st.info(f"**You said:** {speech_text}")

    except Exception as e:

        st.error(f"Speech Recognition Error:\n\n{e}")


# ==========================================================
# TEXT INPUT
# ==========================================================

typed_text = st.chat_input(
    "Ask your question..."
)


# ==========================================================
# FINAL QUESTION
# ==========================================================

question = None

if typed_text and typed_text.strip():

    question = typed_text.strip()

elif speech_text and speech_text.strip():

    question = speech_text.strip()
# ==========================================================
# ASK QUESTION
# ==========================================================

# ==========================================================
# ASK QUESTION
# ==========================================================

# ==========================================================
# ASK QUESTION
# ==========================================================

if question:

    # Prevent duplicate processing
    if st.session_state.get("last_question") != question:

        st.session_state.last_question = question

        try:

            with st.spinner("🤖 Thinking..."):

                answer = ask_question(
                    persona=persona,
                    question=question,
                    uploaded_files=uploaded_files
                )

            st.session_state.last_answer = answer

        except Exception as e:

            st.error(f"Error:\n\n{e}")
# ==========================================================
# DISPLAY LATEST RESPONSE
# ==========================================================

if "last_answer" in st.session_state:

    st.success("✅ Response Generated")


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.markdown(
"""
---
Made with ❤️ using

- Streamlit
- Groq Llama 3
- Groq Whisper
- LangChain
- FAISS
- HuggingFace Embeddings
"""
)
