import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

# --------------------------------------------------
# Load environment
# --------------------------------------------------

load_dotenv()

app = FastAPI(
    title="AI Wellness Backend",
    description="Ayurvedic Stress & Sleep Advisor",
    version="3.0",
)

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # must be False when allow_origins=["*"]
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# --------------------------------------------------
# Groq client
# --------------------------------------------------

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

CATALOG_PATH = Path(__file__).parent / "products.json"

# --------------------------------------------------
# Request models
# --------------------------------------------------


class ChatMessage(BaseModel):
    role: str
    content: str


class WellnessRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


# --------------------------------------------------
# Product catalog
# --------------------------------------------------


def load_catalog() -> list[dict[str, Any]]:
    """
    Loads products from products.json
    """
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            products = json.load(f)

        print(f"Loaded {len(products)} products")

        return products

    except Exception as e:
        print("Catalog loading error:", str(e))
        return []


def format_catalog_for_prompt(products: list[dict]) -> str:
    lines = []

    for p in products:
        tags = ", ".join(p.get("tags", []))

        lines.append(
            f'- {p["handle"]} | {p["name"]} | ₹{p["price"]} | '
            f'{p.get("description", "")} | tags: {tags}'
        )

    return "\n".join(lines)


# --------------------------------------------------
# System prompt
# --------------------------------------------------


def build_system_prompt(products: list[dict]) -> str:
    catalog_block = format_catalog_for_prompt(products)

    return f"""
You are a premium Ayurvedic wellness advisor specialising in stress relief and sleep improvement.

VOICE:
- Warm
- Calm
- Supportive
- Professional
- Short and helpful

AVAILABLE PRODUCTS:
{catalog_block}

RECOMMENDATION GUIDE:
- Stress / anxiety → ashwagandha-stress-relief-capsules, brahmi-mind-relax-oil, shankhpushpi-mind-calm-syrup
- Trouble sleeping → jatamansi-sleep-drops, tagar-deep-sleep-tablets
- Racing thoughts → shankhpushpi-mind-calm-syrup, jatamansi-sleep-drops
- Bedtime relaxation → brahmi-mind-relax-oil, chamomile-sleep-infusion
- Gut discomfort affecting sleep → triphala-detox-sleep-tea
- Strong sleep support → sleep-ritual-wellness-kit

IMPORTANT RULES:
- Recommend ONLY products from catalog
- Never invent products
- Never diagnose disease
- Never claim cures
- Use wording like:
  - "may support relaxation"
  - "may help improve sleep quality"
  - "traditionally used for"

CRITICAL:
Respond ONLY in valid JSON.

Do NOT include:
- markdown
- explanations
- extra text
- code blocks

Correct format:

{{
  "reply": "Warm helpful response",
  "recommended_products": [
    "ashwagandha-stress-relief-capsules"
  ]
}}
"""


# --------------------------------------------------
# Response parser
# --------------------------------------------------


def parse_ai_response(raw: str, catalog: list[dict]):
    """
    Safely parses Groq JSON response
    """

    catalog_index = {
        p["handle"]: p for p in catalog
    }

    def resolve_products(handles):
        products = []

        for handle in handles:
            if handle in catalog_index:
                p = catalog_index[handle]

                products.append({
                    "name": p["name"],
                    "price": p["price"],
                    "handle": p["handle"]
                })

        return products

    try:
        raw = raw.strip()

        # Remove markdown if model adds it
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

        print("\nRAW MODEL RESPONSE:")
        print(raw)

        data = json.loads(raw)

        reply = data.get("reply", "")
        handles = data.get(
            "recommended_products",
            []
        )

        resolved_products = resolve_products(handles)

        return reply, resolved_products

    except Exception as e:
        print("\nJSON PARSE ERROR:")
        print(str(e))
        print("RAW OUTPUT:")
        print(raw)

        return (
            "I’m here to support your sleep and wellness journey. Could you share a little more about how you've been feeling?",
            []
        )


# --------------------------------------------------
# Routes
# --------------------------------------------------


@app.get("/")
def health_check():
    return {
        "status": "running",
        "message": "AI Wellness Backend is Live"
    }


@app.post("/chat")
async def ai_wellness(body: WellnessRequest):
    try:
        catalog = load_catalog()

        system_prompt = build_system_prompt(
            catalog
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Add chat history
        for h in body.history[-10:]:
            messages.append({
                "role": h.role,
                "content": h.content
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": body.message
        })

        completion = (
            groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_tokens=300,
            )
        )

        raw_response = (
            completion
            .choices[0]
            .message.content
        )

        reply, products = (
            parse_ai_response(
                raw_response,
                catalog
            )
        )

        return {
            "success": True,
            "reply": reply,
            "products": products
        }

    except Exception as exc:
        print("\nBACKEND ERROR:")
        print(str(exc))

        return {
            "success": False,
            "reply":
                "Our wellness guide is currently resting. Please try again shortly.",
            "products": [],
            "error": str(exc)
        }