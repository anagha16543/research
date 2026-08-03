import streamlit as st

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from prompts import SALES_PROMPTS
from rag import retrieve_context


# ==========================================================
# LOAD LLM
# ==========================================================

@st.cache_resource
def load_llm():

    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in Streamlit Secrets."
        )

    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.3,
        max_tokens=1024
    )


llm = load_llm()


# ==========================================================
# PROMPT TEMPLATE
# ==========================================================

prompt = ChatPromptTemplate.from_messages(

    [

        (
            "system",
            "{system_prompt}"
        ),

        MessagesPlaceholder(
            variable_name="history"
        ),

        (
            "human",
            "{question}"
        )

    ]

)


# ==========================================================
# LLM CHAIN
# ==========================================================

chain = prompt | llm | StrOutputParser()


# ==========================================================
# INITIALIZE CHAT
# ==========================================================

def initialize_chat():

    if "history" not in st.session_state:

        st.session_state.history = []


# ==========================================================
# CLEAR CHAT
# ==========================================================

def clear_chat():

    st.session_state.history = []


# ==========================================================
# DISPLAY CHAT
# ==========================================================

def display_chat():

    for message in st.session_state.history:

        if isinstance(message, HumanMessage):

            with st.chat_message("user"):

                st.markdown(message.content)

        elif isinstance(message, AIMessage):

            with st.chat_message("assistant"):

                st.markdown(message.content)


# ==========================================================
# ASK QUESTION
# ==========================================================

def ask_question(
    persona,
    question,
    uploaded_files=None
):

    if persona not in SALES_PROMPTS:

        raise ValueError(
            "Invalid Persona Selected."
        )

    context = retrieve_context(
        question,
        uploaded_files
    )

    system_prompt = SALES_PROMPTS[
        persona
    ].format(
        context=context
    )

    answer = chain.invoke(

        {

            "system_prompt": system_prompt,

            "history": st.session_state.history,

            "question": question

        }

    )

    st.session_state.history.append(
        HumanMessage(
            content=question
        )
    )

    st.session_state.history.append(
        AIMessage(
            content=answer
        )
    )

    return answer
