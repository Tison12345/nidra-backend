# Nidra — AI Wellness Backend

FastAPI backend powering the AI Wellness Advisor chat widget on the Nidra Shopify store.

---

## Live URL

```text
https://nidra-backend.onrender.com
```

---

## What It Does

- Receives user messages from the Shopify storefront chat widget
- Builds a context-aware prompt with the live product catalog
- Calls **Groq (LLaMA 3.3 70B)** for fast AI responses
- Returns a structured JSON response with a reply and recommended products
- Maintains up to 10 messages of conversation history per session

---

## Tech Stack

- **FastAPI** — Python web framework
- **Groq API** — LLM inference (LLaMA 3.3 70B)
- **Pydantic** — request/response validation
- **Render** — hosting (free tier)

---

## API Endpoints

### `GET /`

Health check.

```json
{ "status": "running", "message": "AI Wellness Backend is Live" }
```

### `POST /chat`

Main chat endpoint.

**Request:**

```json
{
  "message": "I can't sleep and feel anxious",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "reply": "Ashwagandha may help calm cortisol levels and support deeper sleep...",
  "products": [
    { "name": "Ashwagandha Stress Relief Capsules", "price": 599, "handle": "ashwagandha-stress-relief-capsules" }
  ]
}
```

---

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```text
GROQ_API_KEY=your_key_here
```

Start the server:

```bash
uvicorn main:app --reload
```

Runs at `http://127.0.0.1:8000`

---

## Deploy on Render

1. Connect this repo to [render.com](https://render.com)
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `GROQ_API_KEY`

---

## Shopify Theme Repo

[github.com/Tison12345/nidra-backend](https://github.com/Tison12345/nidra-backend)
