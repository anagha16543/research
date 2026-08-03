import os
import tempfile
import pandas as pd
import streamlit as st

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ==========================================================
# EMBEDDING MODEL
# ==========================================================

@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


embeddings = load_embeddings()


# ==========================================================
# TEXT SPLITTER
# ==========================================================

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)


# ==========================================================
# LOAD DEFAULT FAQ
# ==========================================================

def load_default_excel():

    documents = []

    if os.path.exists("pragyan_faq_prices.xlsx"):

        df = pd.read_excel("pragyan_faq_prices.xlsx")

        for _, row in df.iterrows():

            text = ""

            for column in df.columns:
                text += f"{column}: {row[column]}\n"

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": "FAQ Excel"
                    }
                )
            )

    return documents


# ==========================================================
# LOAD UPLOADED FILES
# ==========================================================

def load_uploaded_files(uploaded_files):

    documents = []

    if not uploaded_files:
        return documents

    for uploaded_file in uploaded_files:

        suffix = os.path.splitext(
            uploaded_file.name
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp:

            temp.write(uploaded_file.read())

            temp_path = temp.name

        try:

            # ---------------- PDF ----------------

            if suffix.lower() == ".pdf":

                loader = PyPDFLoader(temp_path)

                pdf_docs = loader.load()

                documents.extend(pdf_docs)

            # ---------------- EXCEL ----------------

            elif suffix.lower() in [".xlsx", ".xls"]:

                df = pd.read_excel(temp_path)

                for _, row in df.iterrows():

                    text = ""

                    for column in df.columns:
                        text += f"{column}: {row[column]}\n"

                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": uploaded_file.name
                            }
                        )
                    )

        finally:

            os.remove(temp_path)

    return documents


# ==========================================================
# BUILD VECTOR STORE
# ==========================================================

def build_vector_store(uploaded_files=None):

    docs = []

    docs.extend(load_default_excel())

    docs.extend(load_uploaded_files(uploaded_files))

    if len(docs) == 0:

        docs.append(

            Document(

                page_content="""
PragyanAI provides

6 Months Offline Training

followed by

12 Months Internship

and Placement Assistance.
"""

            )

        )

    split_docs = text_splitter.split_documents(docs)

    vectorstore = FAISS.from_documents(
        split_docs,
        embeddings
    )

    st.session_state.vectorstore = vectorstore

    return vectorstore


# ==========================================================
# GET VECTOR STORE
# ==========================================================

def get_vector_store():

    if "vectorstore" not in st.session_state:

        return build_vector_store()

    return st.session_state.vectorstore


# ==========================================================
# RETRIEVE CONTEXT
# ==========================================================

def retrieve_context(question, uploaded_files=None):

    if uploaded_files:

        vectorstore = build_vector_store(uploaded_files)

    else:

        vectorstore = get_vector_store()

    docs = vectorstore.similarity_search(
        question,
        k=4
    )

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    return context


# ==========================================================
# RETRIEVE SOURCES
# ==========================================================

def retrieve_sources(question):

    vectorstore = get_vector_store()

    docs = vectorstore.similarity_search(
        question,
        k=4
    )

    sources = []

    for doc in docs:

        sources.append(
            doc.metadata.get(
                "source",
                "Unknown"
            )
        )

    return list(set(sources))
