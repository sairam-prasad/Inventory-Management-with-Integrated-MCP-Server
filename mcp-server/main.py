import os
import json
import requests
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI

# Load API key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
INVENTORY_API_URL = "http://localhost:8000/inventory"
VALID_ITEMS = ["tshirts", "pants"]

# FastAPI app
app = FastAPI(title="MCP Server – OpenAI + LangChain")

class QueryRequest(BaseModel):
    user_query: str

# Initialize OpenAI
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

@app.post("/query")
def handle_query(request: QueryRequest):
    system_prompt = """
You are an inventory control assistant. You ONLY support two operations:
1. Checking current stock (GET)
2. Updating stock of tshirts or pants (POST)

Return one of the following JSON formats:
{
  "method": "GET"
}
or
{
  "method": "POST",
  "json": {
    "item": "tshirts",
    "change": -3
  }
}

Only valid items are "tshirts" and "pants". Never use any other items.

Interpret intent clearly:
- Actions like "bought", "restocked", "added", "received", or "borrowed" or any other synonyms like this mean INCREASE the count (+).
- Actions like "sold", "used", "gave away", "removed", or "donated" mean DECREASE the count (-).


If the request is unclear, missing, or confusing, reply with:
{
  "method": "ERROR",
  "message": "Could not understand the query. Please mention tshirts or pants clearly."
}
Example:
Input: "I borrowed 3 tshirts"
Output:
{
  "method": "POST",
  "json": {
    "item": "tshirts",
    "change": 3
  }
}
Respond ONLY with raw JSON. No markdown. No explanations.
"""

    try:
        messages: List[BaseMessage] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.user_query)
        ]

        result = llm.invoke(messages)
        content = result.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        print(content)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Could not parse model response. Please try a clearer query like 'I added 5 tshirts'."
            )
        
        if parsed.get("method") == "GET":
            return requests.get(INVENTORY_API_URL).json()

        elif parsed.get("method") == "POST":
            payload = parsed.get("json", {})
            item = payload.get("item")
            if item not in VALID_ITEMS:
                raise HTTPException(status_code=400, detail=f"Invalid item: {item}")
            return requests.post(INVENTORY_API_URL, json=payload).json()

        elif parsed.get("method") == "ERROR":
            raise HTTPException(status_code=400, detail=parsed.get("message"))

        else:
            raise HTTPException(
                status_code=400,
                detail="Model response did not contain a valid operation. Please try again."
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI + LangChain error: {str(e)}")
