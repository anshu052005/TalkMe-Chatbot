import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from langraph_rag_backend import (
    chatbot,
    ingest_pdf,
    retrieve_all_threads,
    thread_document_metadata,
)
from dotenv import load_dotenv
load_dotenv()  # 🌟 Frontend process me bhi saari keys load karne ke liye

# 🌟 Optional: agar backend mein permanent-delete function available hai to use karo.
# Agar nahi hai, to delete sirf is session/UI list se hoga (backend history se nahi).
try:
    from langraph_rag_backend import delete_thread as backend_delete_thread
except ImportError:
    backend_delete_thread = None


# =========================== Page Config ===========================
st.set_page_config(
    page_title="TalkMe AI",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================== Custom Styling ========================
st.markdown(
    """
    <style>
        /* ---- Global ---- */
        .stApp {
            background: linear-gradient(180deg, #0f1117 0%, #12141c 100%);
        }

        /* ---- Hide default Streamlit chrome ---- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* ---- Header / brand block ---- */
        .brand-header {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding-bottom: 0.25rem;
        }
        .brand-title {
            font-size: 2.1rem;
            font-weight: 800;
            background: linear-gradient(90deg, #7C9CFF 0%, #B27CFF 60%, #FF8BD1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        .brand-subtitle {
            color: #9AA3B2;
            font-size: 0.95rem;
            margin-top: -0.4rem;
            margin-bottom: 1.2rem;
        }

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {
            background: #14161f;
            border-right: 1px solid rgba(255,255,255,0.06);
        }
        section[data-testid="stSidebar"] .stButton button {
            border-radius: 10px;
            border: 1px solid rgba(124,156,255,0.35);
            background: rgba(124,156,255,0.08);
            color: #E7EAF3;
            font-weight: 600;
            transition: all 0.15s ease-in-out;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            border-color: #7C9CFF;
            background: rgba(124,156,255,0.18);
            color: #fff;
        }
        .sidebar-section-label {
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 0.72rem;
            color: #7B8496;
            font-weight: 700;
            margin: 1.1rem 0 0.4rem 0;
        }

        /* ---- Chat bubbles ---- */
        div[data-testid="stChatMessage"] {
            border-radius: 14px;
            padding: 0.35rem 0.6rem;
            margin-bottom: 0.35rem;
            border: 1px solid rgba(255,255,255,0.05);
        }

        /* ---- Thread ID pill ---- */
        .thread-pill {
            display: inline-block;
            background: rgba(124,156,255,0.12);
            border: 1px solid rgba(124,156,255,0.3);
            color: #C9D4FF;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-family: monospace;
        }

        /* ---- Divider spacing ---- */
        hr {
            margin: 1.2rem 0;
            opacity: 0.15;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def extract_clean_text(content):
    """
    Model responses (khaaskar tool-calls ke turns) kabhi kabhi content ko
    ek list/dict of blocks (jaise {'type': 'text', 'text': ..., 'extras': {'signature': ...}})
    ke roop mein bhejte hain. Ye function un blocks se sirf readable text
    nikaal deta hai — chahe wo LIVE stream ho ya PURANI chat history se load
    ho raha ho, dono jagah same cleaning lagti hai taaki raw signature/metadata
    kabhi screen par na dikhe.
    """
    # 1. Agar content ek list hai (jaise Gemini signature ke sath bhej raha hai)
    if isinstance(content, list) and len(content) > 0:
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts) if parts else str(content[0])

    # 2. Agar content ek dictionary hai
    if isinstance(content, dict):
        if "text" in content:
            return content["text"]
        if "content" in content:
            return content["content"]
        return str(content)

    # 3. Normal string
    return content


# =========================== Utilities ===========================
def generate_thread_id():
    return uuid.uuid4()


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])


def make_title_from_text(text, max_words=6):
    """First user message se ek chhota, readable title bana deta hai."""
    words = text.strip().split()
    if not words:
        return "New Chat"
    title = " ".join(words[:max_words])
    if len(words) > max_words:
        title += "…"
    return title


def get_thread_title(thread_id):
    """
    Thread ka display title dega:
    1. Agar session mein already cached hai to wahi.
    2. Warna backend se conversation load karke pehla user message dhoondega.
    3. Kuchh na mile to short-id fallback.
    """
    key = str(thread_id)
    titles = st.session_state["thread_titles"]

    if key in titles:
        return titles[key]

    try:
        messages = load_conversation(thread_id)
        for msg in messages:
            if isinstance(msg, HumanMessage) and msg.content:
                title = make_title_from_text(msg.content)
                titles[key] = title
                return title
    except Exception:
        pass

    fallback = f"New Chat · {key[:8]}"
    titles[key] = fallback
    return fallback


def set_thread_title_if_missing(thread_id, text):
    key = str(thread_id)
    if key not in st.session_state["thread_titles"]:
        st.session_state["thread_titles"][key] = make_title_from_text(text)


def delete_thread(thread_id):
    """
    Thread ko UI list, titles aur ingested-doc cache se hata deta hai.
    Agar backend me permanent-delete function available hai, wo bhi try karega.
    """
    key = str(thread_id)

    if thread_id in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].remove(thread_id)

    st.session_state["thread_titles"].pop(key, None)
    st.session_state["ingested_docs"].pop(key, None)

    if backend_delete_thread is not None:
        try:
            backend_delete_thread(key)
        except Exception:
            # Backend delete fail hua to bhi UI se to hat hi jayega.
            pass

    # Agar abhi jo thread active hai wahi delete hua, to naya chat shuru karo.
    if str(st.session_state["thread_id"]) == key:
        reset_chat()


# ======================= Session Initialization ===================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

if "ingested_docs" not in st.session_state:
    st.session_state["ingested_docs"] = {}

if "thread_titles" not in st.session_state:
    st.session_state["thread_titles"] = {}

add_thread(st.session_state["thread_id"])

thread_key = str(st.session_state["thread_id"])
thread_docs = st.session_state["ingested_docs"].setdefault(thread_key, {})
threads = st.session_state["chat_threads"][::-1]
selected_thread = None

# ============================ Sidebar ============================
st.sidebar.markdown(
    """
    <div style="display:flex;align-items:center;gap:0.5rem;padding:0.2rem 0 0.6rem 0;">
        <span style="font-size:1.6rem;">💬</span>
        <span style="font-size:1.25rem;font-weight:800;color:#E7EAF3;">TalkMe AI</span>
    </div>
    """,
    unsafe_allow_html=True,
)

active_title = get_thread_title(st.session_state["thread_id"])
st.sidebar.markdown(
    f'<div class="sidebar-section-label">Active Session</div>'
    f'<span class="thread-pill">{active_title}</span>',
    unsafe_allow_html=True,
)

st.sidebar.write("")
if st.sidebar.button("➕  New Chat", use_container_width=True):
    reset_chat()
    st.rerun()

st.sidebar.markdown('<div class="sidebar-section-label">Document</div>', unsafe_allow_html=True)

if thread_docs:
    latest_doc = list(thread_docs.values())[-1]
    st.sidebar.success(
        f"📄 **{latest_doc.get('filename')}**\n\n"
        f"{latest_doc.get('chunks')} chunks · {latest_doc.get('documents')} pages"
    )
else:
    st.sidebar.info("No PDF indexed yet for this chat.")

uploaded_pdf = st.sidebar.file_uploader(
    "Upload a PDF for this chat", type=["pdf"], help="Indexes the document so you can chat about its contents."
)
if uploaded_pdf:
    if uploaded_pdf.name in thread_docs:
        st.sidebar.info(f"`{uploaded_pdf.name}` already processed for this chat.")
    else:
        with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_key,
                filename=uploaded_pdf.name,
            )
            thread_docs[uploaded_pdf.name] = summary
            status_box.update(label="✅ PDF indexed", state="complete", expanded=False)

st.sidebar.markdown('<div class="sidebar-section-label">Past Conversations</div>', unsafe_allow_html=True)
if not threads:
    st.sidebar.caption("No past conversations yet.")
else:
    thread_to_delete = None
    for thread_id in threads:
        title = get_thread_title(thread_id)
        is_active = str(thread_id) == thread_key
        col_title, col_delete = st.sidebar.columns([5, 1])
        with col_title:
            label = f"💬 {title}" if is_active else f"🕓 {title}"
            if st.button(label, key=f"side-thread-{thread_id}", use_container_width=True):
                selected_thread = thread_id
        with col_delete:
            if st.button("🗑️", key=f"side-delete-{thread_id}", help="Delete this conversation"):
                thread_to_delete = thread_id

    if thread_to_delete is not None:
        delete_thread(thread_to_delete)
        st.rerun()

# ============================ Main Layout ========================
st.markdown(
    """
    <div class="brand-header">
        <span style="font-size:2.1rem;">💬</span>
        <p class="brand-title">TalkMe AI</p>
    </div>
    <p class="brand-subtitle">Your intelligent assistant for documents, tools, and conversation.</p>
    """,
    unsafe_allow_html=True,
)

# Chat area
for message in st.session_state["message_history"]:
    avatar = "🧑‍💻" if message["role"] == "user" else "💬"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

user_input = st.chat_input("Ask about your document or use tools…")

if user_input:
    set_thread_title_if_missing(st.session_state["thread_id"], user_input)
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": thread_key},
        "metadata": {"thread_id": thread_key},
        "run_name": "chat_turn",
    }

    with st.chat_message("assistant", avatar="💬"):
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, _ in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                    
                        )

                if isinstance(message_chunk, AIMessage):
                    # 🌟 Raw JSON/List content ko clean karke sirf text yield karo
                    yield extract_clean_text(message_chunk.content)

        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )

    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )

    doc_meta = thread_document_metadata(thread_key)
    if doc_meta:
        st.caption(
            f"📄 Document indexed: **{doc_meta.get('filename')}** "
            f"· chunks: {doc_meta.get('chunks')} · pages: {doc_meta.get('documents')}"
        )

st.divider()

if selected_thread:
    st.session_state["thread_id"] = selected_thread
    messages = load_conversation(selected_thread)

    temp_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        temp_messages.append({"role": role, "content": extract_clean_text(msg.content)})
    st.session_state["message_history"] = temp_messages
    st.session_state["ingested_docs"].setdefault(str(selected_thread), {})
    st.rerun()