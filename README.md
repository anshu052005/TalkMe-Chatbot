# 💬 TalkMe AI

**TalkMe AI** is a multi-utility AI chatbot built with **LangGraph**, **Streamlit**, and **Groq**. It combines conversational AI with document intelligence (RAG over your own PDFs), web search, live stock prices, and a calculator — all wrapped in a clean, multi-thread chat interface with persistent conversation history.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- 🧠 **Conversational agent** powered by [Groq](https://groq.com/) (`llama-3.3-70b-versatile`) via LangChain
- 📄 **Chat with your PDFs** — upload a document per chat thread and ask questions grounded in its content (RAG with FAISS + HuggingFace embeddings)
- 🔧 **Built-in tools**
  - 🌐 Web search (DuckDuckGo)
  - 📈 Live stock price lookup (Alpha Vantage)
  - 🧮 Calculator (add / sub / mul / div)
  - 📚 Document retriever (`rag_tool`) scoped per chat thread
- 🧵 **Multi-thread conversations** with persistent history (SQLite-backed via LangGraph checkpointer)
- 🏷️ **Auto-named chats** — each conversation is automatically titled from its first message
- 🗑️ **Delete conversations** — remove old threads permanently (both from the UI and the underlying checkpoint database)
- ⚡ **Streaming responses** with live tool-usage indicators (e.g. "🔧 Using `rag_tool`…")
- 🎨 Clean, modern dark-themed UI

---

## 🏗️ Architecture

```
┌─────────────────────┐        ┌──────────────────────────┐
│   Streamlit UI       │  ───▶  │   LangGraph StateGraph    │
│ (frontend.py)        │        │ (langraph_rag_backend.py) │
│                      │        │                            │
│ - Chat interface     │        │  chat_node ──▶ tools_node  │
│ - PDF uploader       │  ◀───  │     ▲              │       │
│ - Thread sidebar     │        │     └──────────────┘       │
└─────────────────────┘        └──────────────────────────┘
                                        │
                     ┌──────────────────┼──────────────────┐
                     ▼                  ▼                  ▼
              SQLite Checkpointer   FAISS Vector Store   External Tools
              (chatbot.db)          (per-thread PDF)      (Search / Stocks)
```

---

## 📁 Project Structure

```
.
├── frontend.py               # Streamlit UI (chat, sidebar, PDF upload, thread management)
├── langraph_rag_backend.py   # LangGraph agent, tools, RAG pipeline, checkpointing
├── chatbot.db                 # SQLite database for conversation persistence (auto-created)
├── requirements.txt           # Python dependencies
├── .env                        # API keys (not committed)
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/talkme-ai.git
cd talkme-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

<details>
<summary>📦 Don't have a <code>requirements.txt</code> yet? Click to expand a starting point.</summary>

```
streamlit
langgraph
langgraph-checkpoint-sqlite
langchain-core
langchain-community
langchain-groq
langchain-huggingface
langchain-text-splitters
sentence-transformers
faiss-cpu
pypdf
duckduckgo-search
requests
python-dotenv
```
</details>

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

> 🔑 Get a free Groq API key at [console.groq.com](https://console.groq.com/) and a free Alpha Vantage key at [alphavantage.co](https://www.alphavantage.co/support/#api-key).

### 5. Run the app

```bash
streamlit run frontend.py
```

The app will open at `http://localhost:8501` 🎉

---

## 🧑‍💻 Usage

1. **Start a new chat** using the "➕ New Chat" button in the sidebar.
2. **Upload a PDF** (optional) — it gets indexed for that specific conversation only.
3. **Ask anything** — general questions, questions about your PDF, stock prices, or math calculations. The agent automatically decides which tool to use.
4. **Switch between conversations** from the sidebar — each is auto-titled from its first message.
5. **Delete a conversation** anytime using the 🗑️ button next to it — this removes it from both the UI and the persistent database.

---

## 🛠️ Tech Stack

| Layer            | Technology                                      |
|-------------------|--------------------------------------------------|
| UI                | [Streamlit](https://streamlit.io/)               |
| Agent orchestration | [LangGraph](https://www.langchain.com/langgraph) |
| LLM               | [Groq](https://groq.com/) (`llama-3.3-70b-versatile`) |
| Embeddings        | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store      | [FAISS](https://github.com/facebookresearch/faiss) |
| Persistence       | SQLite (`langgraph-checkpoint-sqlite`)           |
| Web search        | DuckDuckGo Search                                 |
| Stock data        | Alpha Vantage API                                 |

---

## ⚠️ Notes & Limitations

- PDF retrievers are stored **in memory** — restarting the app clears indexed documents (conversation history itself persists via SQLite).
- `SqliteSaver` is intended for lightweight/single-user use. For production or multi-user deployments, consider swapping in `PostgresSaver`.
- Avoid committing your `.env` file or `chatbot.db` (containing personal conversation history) to version control — see [`.gitignore`](#-gitignore) below.

## 📄 .gitignore

```gitignore
.env
chatbot.db
__pycache__/
*.pyc
venv/
.streamlit/
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](../../issues) or open a pull request.

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">Made with ❤️ using LangGraph + Streamlit</p>
