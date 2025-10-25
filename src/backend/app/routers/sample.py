from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from app.models.schemas import Item, ItemCreate, ItemUpdate

# Create router instance
router = APIRouter()

# In-memory storage for demo purposes
items_db = []
item_counter = 0


@router.get("/items", response_model=List[Item])
async def get_items():
    """
    Get all items from the database.
    """
    return items_db


@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """
    Get a specific item by ID.
    """
    for item in items_db:
        if item["id"] == item_id:
            return item
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    """
    Create a new item.
    """
    global item_counter
    item_counter += 1
    
    new_item = {
        "id": item_counter,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "is_available": item.is_available,
        "created_at": datetime.now()
    }
    
    items_db.append(new_item)
    return new_item


@router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemUpdate):
    """
    Update an existing item.
    """
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            # Update only provided fields
            update_data = item_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                items_db[i][field] = value
            
            return items_db[i]
    
    raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """
    Delete an item by ID.
    """
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            deleted_item = items_db.pop(i)
            return {"message": f"Item '{deleted_item['name']}' deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Item not found")


# Add some sample data
@router.post("/items/seed")
async def seed_sample_data():
    """
    Add some sample items to the database for testing.
    """
    global item_counter
    
    sample_items = [
        ItemCreate(
            name="Laptop",
            description="High-performance laptop for development",
            price=1299.99,
            is_available=True
        ),
        ItemCreate(
            name="Mouse",
            description="Wireless optical mouse",
            price=29.99,
            is_available=True
        ),
        ItemCreate(
            name="Keyboard",
            description="Mechanical keyboard with RGB lighting",
            price=149.99,
            is_available=False
        )
    ]
    
    created_items = []
    for item_data in sample_items:
        item_counter += 1
        new_item = {
            "id": item_counter,
            "name": item_data.name,
            "description": item_data.description,
            "price": item_data.price,
            "is_available": item_data.is_available,
            "created_at": datetime.now()
        }
        items_db.append(new_item)
        created_items.append(new_item)
    
    return {"message": f"Created {len(created_items)} sample items", "items": created_items}
