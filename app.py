import streamlit as st
import time
from datetime import datetime
import logging

# Import RAG Service
from rag_service import RAGService
from config import GOOGLE_API_KEY

# ------------------ Initialize RAG Service ------------------
@st.cache_resource
def get_rag_service():
    """Initialize and cache RAG service."""
    try:
        return RAGService()
    except Exception as e:
        st.error(f"Error initializing RAG service: {str(e)}")
        return None

rag_service = get_rag_service()

if not rag_service:
    st.error("⚠️ Failed to initialize RAG service. Please check your configuration.")
    st.stop()

if not GOOGLE_API_KEY:
    st.error("⚠️ GOOGLE_API_KEY not found! Please define GOOGLE_API_KEY variable in .env file.")
    st.stop()

# ------------------ Main Function ------------------
def generate_medical_response(complaint):
    """Generate medical response using RAG service."""
    if not rag_service:
        return {
            "response": "[Error] RAG service not available.",
            "sources": [],
            "context": "",
            "metadata": {}
        }
    
    return rag_service.process_query(complaint)

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
        with st.spinner("Processing query through RAG pipeline..."):
            result = generate_medical_response(user_input)
            # Check for backward compatibility
            if isinstance(result, dict):
                response_text = result["response"]
                sources = result.get("sources", [])
                context = result.get("context", "")
                metadata = result.get("metadata", {})
                execution_trace = result.get("execution_trace", None)
            else:
                response_text = result
                sources = []
                context = ""
                metadata = {}
                execution_trace = None
            
            history.append({
                "role": "assistant", 
                "content": response_text,
                "sources": sources,
                "context": context,
                "metadata": metadata,
                "execution_trace": execution_trace
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
                    with st.expander("🔍 Sources from Milvus Vectorstore (First 500 characters)"):
                        st.info(f"✅ {len(sources)} documents found and used")
                        for i, source in enumerate(sources, 1):
                            st.markdown(f"**Source {i}:**")
                            st.text(source)
                            st.markdown("---")
                
                # Show execution trace if available (Agentic RAG)
                if role == "assistant" and msg.get("execution_trace"):
                    with st.expander("🤖 Agentic RAG Execution Trace"):
                        trace = msg["execution_trace"]
                        st.json({
                            "iterations": trace.get("iterations", 0),
                            "plan": trace.get("plan", {}).get("task_type", "unknown")
                        })
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
                        with st.expander("🔍 Sources from Milvus Vectorstore (First 500 characters)"):
                            st.info(f"✅ {len(sources)} documents found and used")
                            for i, source in enumerate(sources, 1):
                                st.markdown(f"**Source {i}:**")
                                st.text(source)
                                st.markdown("---")
                    
                    # Show execution trace if available (Agentic RAG)
                    if msg.get("execution_trace"):
                        with st.expander("🤖 Agentic RAG Execution Trace"):
                            trace = msg["execution_trace"]
                            st.json({
                                "iterations": trace.get("iterations", 0),
                                "plan": trace.get("plan", {}).get("task_type", "unknown")
                            })
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
