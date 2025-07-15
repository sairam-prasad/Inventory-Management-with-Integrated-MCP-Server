from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app with a title for docs
app = FastAPI(title="Inventory Web Service")

# Enable CORS so this service can be called from the MCP server running on another port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, use a specific origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store to track inventory (meets task requirement)
# Chose dict for simplicity and fast O(1) lookups/updates
inventory = {"tshirts": 20, "pants": 15}

# Input model to ensure well-structured POST body
class InventoryChangeRequest(BaseModel):
    item: str
    change: int

# GET endpoint returns full inventory status
@app.get("/inventory")
def get_inventory():
    return inventory

# POST endpoint updates inventory for a given item
@app.post("/inventory")
def update_inventory(request: InventoryChangeRequest):
    item = request.item.lower()

    # Validate item type
    if item not in inventory:
        raise HTTPException(status_code=400, detail="Invalid item")

    # Prevent negative inventory values (logical business rule)
    new_count = inventory[item] + request.change
    if new_count < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock: only {inventory[item]} {item} left"
        )

    # Update inventory and return current state
    inventory[item] = new_count
    return inventory
