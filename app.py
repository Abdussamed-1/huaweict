import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# ------------------ Environment Variables ------------------
load_dotenv()

# ------------------ API Keys ------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("⚠️ GOOGLE_API_KEY not found! Please define GOOGLE_API_KEY variable in .env file.")
    st.stop()

# ------------------ VectorStore and Embedding ------------------
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
VECTORSTORE_DIR = r"C:\Users\samet\OneDrive\Belgeler\GitHub\Chatbot-Project\project\yeni\medical_vectorstore"
vectorstore = Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=embedding_model)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ------------------ LLM and Prompt ------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=GOOGLE_API_KEY)

template = """
You are an experienced medical assistant supporting a doctor in evaluating a patient’s symptoms. Based on the provided context and the doctor’s question, respond clearly and professionally. Do not copy the context directly—paraphrase and interpret it to generate a medically sound, structured answer.

Your response **must** be divided into three clear paragraphs:
1. **Diagnosis**: State the most likely medical diagnosis using precise terminology.
2. **Clinical Reasoning**: Explain key findings from the context that support this diagnosis.
3. **Interpretation**: Provide guidance to help the doctor link the diagnosis to the patient’s symptoms.

**Strict Content Guidelines**:
- If the input is unrelated to healthcare, diagnosis, or symptoms (e.g., general knowledge, greetings, names), reply:
  > "This system is designed exclusively for medical diagnostic assistance; I cannot answer unrelated questions."
- If the input lacks sufficient clinical detail (e.g., "I have a headache" without additional information), reply:
  > "More clinical information is required; please elaborate on symptoms and findings."

**Retrieval Check**:
- If there is no relevant medical context (e.g., retrieved documents list is empty or similarity scores are below threshold), reply:
  > "I’m sorry, I couldn’t find enough relevant medical information to answer your question. Could you please provide more details about the patient’s history and symptoms?"

Context:
{context}

Doctor’s Question:
{question}

Respond only with the three paragraphs described. Do not add any extra sections or disclaimers.
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | llm

# ------------------ Main Function ------------------
def generate_medical_response(complaint):
    try:
        docs = retriever.invoke(complaint)
        if not docs:
            return {
                "response": "[Warning] Relevant context not found.",
                "sources": [],
                "context": ""
            }

        # Get context directly from page content
        context = "\n\n".join([
            doc.page_content for doc in docs
        ])

        # Continue with LLM call even if still empty:
        # context = "" assignment ensures chain.invoke still works.
        if not context.strip():
            context = ""

        response = chain.invoke({
            "question": complaint,
            "context": context
        })

        if not response.content.strip():
            return {
                "response": "[Warning] Model did not return a response.",
                "sources": [],
                "context": context
            }

        # Prepare source documents (first 500 characters)
        sources = [doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content 
                   for doc in docs]

        return {
            "response": response.content,
            "sources": sources,
            "context": context[:1000] + "..." if len(context) > 1000 else context  # First 1000 characters
        }

    except Exception as e:
        return {
            "response": f"[GENERAL ERROR] {str(e)}",
            "sources": [],
            "context": ""
        }

# ------------------ Chat UI and Chat History ------------------
st.set_page_config(page_title="Health Assistant", layout="centered")

# --- Delete callback ---
def delete_chat(chat_id):
    st.session_state.chat_sessions.pop(chat_id, None)
    st.session_state.chat_titles.pop(chat_id, None)
    st.session_state.chat_last_index.pop(chat_id, None)
    # If active chat is deleted, switch to one of the remaining ones
    if st.session_state.active_chat == chat_id:
        remaining = list(st.session_state.chat_sessions.keys())
        st.session_state.active_chat = remaining[0] if remaining else None

# --- Menu ---
if "page" not in st.session_state:
    st.session_state.page = "Welcome"
st.sidebar.markdown("🔍 Menu")
if st.sidebar.button("Welcome"):
    st.session_state.page = "Welcome"
if st.sidebar.button("Chat"):
    st.session_state.page = "Chat"
if st.sidebar.button("Help"):
    st.session_state.page = "Help"
page = st.session_state.page

# --- Initialize Common State ---
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions    = {}
if "chat_titles" not in st.session_state:
    st.session_state.chat_titles      = {}
if "chat_last_index" not in st.session_state:
    st.session_state.chat_last_index  = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat      = None
if "default_chat_id" not in st.session_state:
    st.session_state.default_chat_id  = None

# --- Create Default Chat (if none exists) ---
if not st.session_state.chat_sessions:
    default_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.chat_sessions[default_id]   = []
    st.session_state.chat_titles[default_id]     = "Chat"
    st.session_state.chat_last_index[default_id] = 0
    st.session_state.active_chat                 = default_id
    st.session_state.default_chat_id             = default_id

# --- 1) Welcome ---
if page == "Welcome":
    st.title("🩺 AI Health Assistant")
    st.markdown(
        """
        Hello!  
        With this application, you can write your complaint and get answers for possible diagnoses.  
        Start by navigating to the **Chat** page from the menu on the left.
        """
    )
    st.markdown("---")
    st.markdown(
        """
        ❗ **Warning:**  
        This AI-powered health chatbot is designed solely for informational purposes and to support the diagnostic process. 
        The ultimate responsibility for clinical decision-making lies with the physician. The responses provided by the chatbot 
        cannot replace the doctor's medical evaluation and decisions; they should only be used as a supporting tool. Therefore, 
        system developers or providers cannot be held responsible for consequences arising from decisions made based on the chatbot's recommendations.
        """
    )

# --- 2) Chat ---
elif page == "Chat":
    st.title("🗣️ Health Chat")

    # 2.1) New Chat Button
    if st.sidebar.button("➕ New Chat"):
        new_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.chat_sessions[new_id]   = []
        st.session_state.chat_titles[new_id]     = "Chat"
        st.session_state.chat_last_index[new_id] = 0
        st.session_state.active_chat             = new_id

    # 2.2) Chat History Buttons and Delete
    st.sidebar.markdown("### Chat History")
    for chat_id in list(st.session_state.chat_sessions.keys()):
        cols = st.sidebar.columns([4, 1])
        # Title button
        if cols[0].button(
            st.session_state.chat_titles.get(chat_id, "Chat"),
            key=f"select_{chat_id}"
        ):
            st.session_state.active_chat = chat_id
        # Delete button: only this chat_id is deleted
        cols[1].button(
            "🗑️",
            key=f"delete_{chat_id}",
            on_click=delete_chat,
            args=(chat_id,)
        )

    # Active chat data
    active     = st.session_state.active_chat
    history    = st.session_state.chat_sessions.get(active, [])
    last_index = st.session_state.chat_last_index.get(active, 0)

    # 2.3) User Input
    user_input = st.chat_input("Enter your complaint and press Enter:")
    if user_input:
        if last_index == 0:
            words   = user_input.split()
            summary = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
            date    = datetime.now().strftime("%d %b %Y")
            st.session_state.chat_titles[active] = f"{summary} - {date}"

        history.append({"role": "user",      "content": user_input})
        with st.spinner("Analyzing text..."):
            result = generate_medical_response(user_input)
            # Check for backward compatibility
            if isinstance(result, dict):
                response_text = result["response"]
                sources = result.get("sources", [])
                context = result.get("context", "")
            else:
                response_text = result
                sources = []
                context = ""
            
            history.append({
                "role": "assistant", 
                "content": response_text,
                "sources": sources,
                "context": context
            })

    # 2.4) Display Messages
    for idx, msg in enumerate(history):
        # Backward compatibility - msg should always be dict but let's check
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role", "user")
        
        if idx < last_index:
            with st.chat_message(role):
                content = msg.get("content", msg.get("response", ""))
                sources = msg.get("sources", [])
                st.markdown(content)
                # Show vectorstore sources
                if role == "assistant" and sources:
                    with st.expander("🔍 Sources from Vectorstore (First 500 characters)"):
                        st.info(f"✅ {len(sources)} documents found and used")
                        for i, source in enumerate(sources, 1):
                            st.markdown(f"**Source {i}:**")
                            st.text(source)
                            st.markdown("---")
        else:
            with st.chat_message(role):
                if role == "assistant":
                    content = msg.get("content", msg.get("response", ""))
                    sources = msg.get("sources", [])
                    display = st.empty()
                    typed   = ""
                    for para in content.split("\n\n"):
                        for word in para.split():
                            typed += word + " "
                            display.markdown(typed)
                            time.sleep(0.05)
                        typed += "\n\n"
                    
                    # Show vectorstore sources
                    if sources:
                        with st.expander("🔍 Sources from Vectorstore (First 500 characters)"):
                            st.info(f"✅ {len(sources)} documents found and used")
                            for i, source in enumerate(sources, 1):
                                st.markdown(f"**Source {i}:**")
                                st.text(source)
                                st.markdown("---")
                else:
                    content = msg.get("content", "")
                    st.markdown(content)

    # 2.5) Update index
    st.session_state.chat_last_index[active] = len(history)

# --- 3) Help ---
else:
    st.title("❓ Help")
    st.markdown(
        """
        **How to Use?**  
        - **➕ New Chat**: Starts a new dialogue.  
        - Click on chat titles on the left to return to previous conversations.  
        - Each chat title has a 🗑️ button next to it; you can delete it by clicking.  
        - Each chat title is updated with a summary of your first complaint and the date.

        **FAQ**  
        - *Why do I only see my last complaint?*  
          The code only shows newly added messages with animation, displaying history statically at once.
        """
    )
