# RAG Pipeline Flow

This project has two related flows:

1. An offline ingestion flow in [backend/rag/ingestion.py](/home/abhishek/Documents/projects/rag chatbot/backend/rag/ingestion.py)
2. A live chat flow in [backend/app.py](/home/abhishek/Documents/projects/rag chatbot/backend/app.py) and [backend/rag/chatbot.py](/home/abhishek/Documents/projects/rag chatbot/backend/rag/chatbot.py)

They are connected conceptually, but in the current code the live chat flow does **not** read from the Chroma vector database created by the ingestion script.

## High-Level Flow

```text
User types question in frontend
  -> frontend/app.js sends POST /chat
  -> backend/app.py receives the question
  -> backend/rag/chatbot.py loads portfolio text sections
  -> chatbot.py ranks sections by keyword overlap
  -> top sections are combined into context
  -> Groq LLM is called with prompt + context
  -> answer is returned as JSON
  -> frontend renders the response
```

## 1. Frontend Request Flow

File: [frontend/app.js](/home/abhishek/Documents/projects/rag chatbot/frontend/app.js)

- The chat form listens for submit events.
- When the user sends a message, the frontend:
  - reads the text from the input
  - appends the user message to the UI
  - sends a `POST` request to `/chat` with JSON like:

```json
{ "question": "your question here" }
```

- While waiting, it shows `"Thinking..."`.
- When the backend responds, it displays `data.answer`.

## 2. Flask API Flow

File: [backend/app.py](/home/abhishek/Documents/projects/rag chatbot/backend/app.py)

- `GET /` serves `frontend/index.html`
- `POST /chat`:
  - reads JSON from the request body
  - extracts `question`
  - calls `get_response(question)`
  - returns:

```json
{ "answer": "..." }
```

So `app.py` is only the API layer. The RAG logic lives in `chatbot.py`.

## 3. Live Retrieval and Generation Flow

File: [backend/rag/chatbot.py](/home/abhishek/Documents/projects/rag chatbot/backend/rag/chatbot.py)

This is the actual runtime pipeline used by `/chat`.

### Step A: Input validation

- `get_response(question)` trims the incoming question.
- If the question is empty, it returns:
  - `"Ask a question about Abhishek's portfolio."`

### Step B: Load source data

- `_load_sections()` reads:
  - `backend/model/data/portfolio_rag.txt`
- The file is split into sections using blank lines.
- Each section becomes one retrievable unit.

So the current knowledge base is not a database query. It is a plain text file split into paragraphs/sections.

### Step C: Retrieve relevant context

- The user question is tokenized with `re.findall(r"\w+", ...)`
- Each section is tokenized the same way.
- `_score_section()` scores a section by counting how many words overlap between:
  - the question terms
  - the section terms

Then:

- all sections are sorted by score descending
- the top 3 sections are selected
- those sections are joined into a single `context` string

This is the current "retrieval" step.

It is RAG-like, but not vector retrieval. It is simple lexical matching.

### Step D: Create the LLM client

- `_get_llm()` checks `GROQ_API_KEY`
- If the key is missing, the function returns `None`
- If present, it creates:

```python
ChatGroq(model_name="llama-3.3-70b-versatile")
```

### Step E: Generate the answer

- A prompt is built with:
  - system-style behavior instructions
  - the retrieved context
  - the user question

The model is instructed to:

- act as Abhishek's AI assistant
- speak confidently and sarcastically
- answer only from the provided context

- `llm.invoke(...)` sends the prompt to Groq
- The returned message content becomes the final answer

## 4. Offline Ingestion Flow

File: [backend/rag/ingestion.py](/home/abhishek/Documents/projects/rag chatbot/backend/rag/ingestion.py)

This file builds a vector store, but that vector store is not currently used by `chatbot.py`.

### What ingestion.py does

1. Loads `.txt` files from:
   - `backend/model/data`
2. Splits the loaded documents into chunks using:
   - `chunk_size=500`
   - `chunk_overlap=100`
3. Creates embeddings with:
   - `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")`
4. Stores the embedded chunks in a Chroma database at:
   - `backend/model/chroma_db`
5. Persists the database to disk

### Intended purpose

This script is the indexing stage of a standard vector-based RAG pipeline:

```text
raw text files
  -> split into chunks
  -> convert chunks to embeddings
  -> store embeddings in Chroma
```

## 5. Important Architectural Note

Right now the project is **not** using the Chroma database during chat.

That means:

- `ingestion.py` creates embeddings and stores them
- `chatbot.py` ignores that store completely
- live retrieval uses keyword overlap on `portfolio_rag.txt`

So the current runtime pipeline is:

```text
Question
  -> keyword match against text sections
  -> top 3 sections
  -> LLM answer
```

Not:

```text
Question
  -> embed question
  -> similarity search in Chroma
  -> retrieve best chunks
  -> LLM answer
```

## 6. End-to-End Sequence

### What happens when a user asks a question

1. The browser sends the question to `POST /chat`.
2. Flask extracts the question.
3. `get_response()` loads sections from `portfolio_rag.txt`.
4. The question terms are compared against each section.
5. The best 3 sections are selected as context.
6. Groq `llama-3.3-70b-versatile` receives the prompt.
7. The generated answer is returned to Flask.
8. Flask returns JSON to the browser.
9. The frontend displays the answer.

## 7. Why This Matters

This distinction is important because the repo looks like a vector RAG project, but the actual chat path is simpler:

- ingestion is vector-based
- answering is keyword-based

If you want a true vector RAG flow, `chatbot.py` would need to:

1. load the persisted Chroma store
2. embed the user question
3. run similarity search
4. use the retrieved chunks as context
5. send that context to the LLM

## 8. Short Summary

- `frontend/app.js` sends the question
- `backend/app.py` exposes the chat API
- `backend/rag/chatbot.py` performs the current retrieval and generation
- `backend/rag/ingestion.py` builds a Chroma vector DB offline
- the current live pipeline does **not** use that vector DB

So this project is currently a hybrid setup: it contains vector-ingestion code, but the active chatbot flow uses file-based keyword retrieval.
