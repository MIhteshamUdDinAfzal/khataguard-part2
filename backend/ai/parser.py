import json
import os
from openai import OpenAI

DEFAULT_MODEL = "openai/gpt-oss-20b"


def get_ai_client(api_key=None):
    api_key = api_key or os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=45,
        max_retries=1,
    )


def parse_transaction(
    text,
    api_key=None,
    model=DEFAULT_MODEL
):
    if not text or not text.strip():
        raise ValueError("Transaction text cannot be empty.")

    client = get_ai_client(api_key)

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        max_completion_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": """
Extract ONE customer sale/payment from Urdu,
Roman Urdu or English.

Return ONLY JSON:

{
    "customer": "string",
    "sale": number,
    "paid": number,
    "needs_clarification": boolean,
    "question": "string"
}

Rules:

- sale = NEW goods/services value.
- paid = money received NOW.
- Payment-only transaction has sale = 0.
- Do not convert previous balance into a new sale.
- Never invent missing customer or amount.
- Only process ONE customer at a time.
- Multiple customers require clarification.
- Ambiguous transactions require clarification.
- Refunds, corrections and discounts require clarification.
- Amounts are in Pakistani Rupees.

Important:

AI only understands the user's sentence.
AI does NOT calculate the final customer balance.
AI does NOT save anything to the database.

Example:

Ahmed ne 5000 ka saman liya aur 2000 de diye.

Return:

{
    "customer": "Ahmed",
    "sale": 5000,
    "paid": 2000,
    "needs_clarification": false,
    "question": ""
}
"""
            },
            {
                "role": "user",
                "content": text.strip()[:6000]
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON.")

    return data
