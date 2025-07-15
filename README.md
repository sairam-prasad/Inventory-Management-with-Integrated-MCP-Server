# Inventory Management with Integrated MCP Server

This project is a backend system that combines traditional RESTful API design with a GenAI-powered natural language interface. It was developed as part of a technical internship evaluation to demonstrate the ability to build modular backend services, integrate LLMs into workflows, and handle realistic edge cases.

## Overview

The system includes two independent services:

1. **Inventory Web Service**  
   - Tracks inventory for `tshirts` and `pants`
   - Provides two endpoints:  
     - `GET /inventory` – Returns current stock  
     - `POST /inventory` – Modifies stock based on request

2. **Model Control Plane (MCP) Server**  
   - Accepts natural language queries (e.g., "I sold 4 tshirts")  
   - Converts them into structured API calls using a language model (Gemma via OpenRouter)
   - Calls the appropriate endpoint on the Inventory Web Service


## Technologies Used

- Python 3.10+
- FastAPI
- OpenRouter (LLM: Gemma)
- Requests
- Pydantic
- dotenv for environment variables

##  Setup Instructions 

1. git clone https://github.com/sairam-prasad/Inventory-Management-with-Integrated-MCP-Server.git
2. cd Inventory-Management-with-Integrated-MCP-Server
3. Run inventory service  
  cd inventory-service  
  pip install -r requirements.txt  
  uvicorn main:app --reload --port 8000  
4. Run MCP server  
   cd ../mcp-server  
   pip install -r requirements.txt  
   create a .env file inside MCP server and include OPENROUTER_API_KEY=your_openrouter_api_key  
   uvicorn main:app --reload --port 9000  

## Postman endpoints 

1. Get current Inventory - curl -X GET http://localhost:8000/inventory

Expected Response 
{
  "tshirts": 20,
  "pants": 15
}

2. Add items to the inventory
  curl -X POST http://localhost:8000/inventory \
    -H "Content-Type: application/json" \
    -d '{"item": "tshirts", "change": 5}'

  Expected Outcome : This increases the tshirts count by 5.

3. Remove Items from Inventory
   curl -X POST http://localhost:8000/inventory \
    -H "Content-Type: application/json" \
    -d '{"item": "pants", "change": -3}'
 
 Expected Outcome:  This decreases the pants count by 3.

4. Invalid Item Request
   curl -X POST http://localhost:8000/inventory \
    -H "Content-Type: application/json" \
    -d '{"item": "shoes", "change": 2}'

Expected Outcome: 400 Bad Request with detail: "Invalid item"

5. Remove More than available
   curl -X POST http://localhost:8000/inventory \
    -H "Content-Type: application/json" \
    -d '{"item": "pants", "change": -9999}'

6. Query to check Inventory
   curl -X POST http://localhost:9000/query \
    -H "Content-Type: application/json" \
    -d '{"user_query": "How many tshirts and pants do I have?"}'
   Expected: JSON showing current counts.

7. Query to add Items
   curl -X POST http://localhost:9000/query \
    -H "Content-Type: application/json" \
    -d '{"user_query": "Add 10 tshirts"}'

  Expected: Adds 10 tshirts via GenAI-to-API logic.

8. Query to sell items
   curl -X POST http://localhost:9000/query \
    -H "Content-Type: application/json" \
    -d '{"user_query": "I sold 3 pants"}'

  Expected: Subtracts 3 pants via LLM interpretation.

9. Query using Synonym
   curl -X POST http://localhost:9000/query \
    -H "Content-Type: application/json" \
    -d '{"user_query": "I gave away 2 tshirts"}'

Expected: Should trigger a POST with change: -2 based on prompt logic.

10. Invalid/Unclear Query Handling
  curl -X POST http://localhost:9000/query \
    -H "Content-Type: application/json" \
    -d '{"user_query": "blllahhhh"}'

  Expected: 400 or 500 error with detail indicating that the LLM output couldn't be parsed or understood.




