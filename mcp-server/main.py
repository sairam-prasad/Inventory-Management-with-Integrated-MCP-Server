import os
import requests
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load OpenRouter API key from .env (secure practice)
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Initialize FastAPI for the MCP (GenAI control layer)
app = FastAPI(title="MCP Server – GenAI Control Plane")

# Inventory API URL this MCP server will control
INVENTORY_API_URL = "http://localhost:8000/inventory"

# Input model for user query from frontend or CLI
class QueryRequest(BaseModel):
    user_query: str

@app.post("/query")
def handle_query(request: QueryRequest):
    # Prompt is carefully designed to:
    # - generalize to many verbs (add, buy, ship, etc.)
    # - assume user is managing inventory (clarifies intent)
    # - output only JSON (easy to parse)
    prompt = f"""
You are a backend controller assistant for an inventory system.

You receive natural language queries related to two items: "tshirts" and "pants".

Your task is to return a JSON object with:
- "method": either "GET" or "POST"
- If "POST", include a "json" object with:
    - "item": one of "tshirts" or "pants"
    - "change": an integer:
        - Positive if inventory is increased (e.g., restocked, added, bought, received)
        - Negative if inventory is decreased (e.g., sold, gave away, shipped, used, removed)

Assume:
- The user is managing their own inventory.
- Interpret intent from context, even if synonyms or indirect phrases are used.
- Do not ask follow-up questions.

Respond with only a raw JSON object. No explanations. No markdown.
Query: "{request.user_query}"
"""

    try:
        # Prepare request to OpenRouter to call LLM (Gemma free-tier)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "google/gemma-3n-e2b-it:free",
            "messages": [{"role": "user", "content": prompt}]
        }

        # Send request to LLM
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        # Parse LLM response
        data = response.json()
        print(data)
        gen_response = data["choices"][0]["message"]["content"].strip()
        print("LLM Response:\n", gen_response)

        # Case 1: "GET" request, directly return current inventory
        if "GET" in gen_response:
            return requests.get(INVENTORY_API_URL).json()

        # Case 2: "POST" – inventory modification request
        elif "POST" in gen_response:
            import re

            # Try to extract raw JSON block (supporting Markdown-wrapped or plain text)
            match = re.search(r'```json\s*({.*?})\s*```', gen_response, re.DOTALL)
            if match:
                payload_str = match.group(1)
            else:
                # Fallback: find first {...} block
                payload_start = gen_response.find("{")
                payload_end = gen_response.rfind("}")
                payload_str = gen_response[payload_start:payload_end+1]

            # Parse extracted JSON string
            try:
                payload = json.loads(payload_str)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not parse JSON payload: {e}")

            # Validate and forward the payload to the inventory service
            if payload.get("method") == "POST" and "json" in payload:
                return requests.post(INVENTORY_API_URL, json=payload["json"]).json()
            else:
                raise HTTPException(status_code=400, detail="Invalid structure in LLM response")

        else:
            # Handle unexpected or incomplete responses
            raise HTTPException(status_code=400, detail="Could not parse response")

    except Exception as e:
        # Fallback error handler for debugging or network errors
        raise HTTPException(status_code=500, detail=str(e))
