from fastapi import HTTPException

def get_or_404(session, model, item_id):
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(404, "Item not found")
    return item
