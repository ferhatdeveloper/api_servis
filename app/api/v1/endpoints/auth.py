from fastapi import APIRouter, HTTPException, Depends
from app.core.database import db_manager
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

from app.core.security import verify_password

@router.post("/login")
async def login(req: LoginRequest):
    query = "SELECT id, username, full_name, role, password_hash, logo_salesman_code, email FROM users WHERE username = %s"
    user_row = db_manager.execute_pg_query(query, (req.username,))
    
    if not user_row:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # user_row structure: (id, username, full_name, role, password_hash, ...)
    # Indices: 0:id, 1:username, 2:full_name, 3:role, 4:password_hash
    
    user_data = user_row[0]
    stored_hash = user_data["password_hash"] if isinstance(user_data, dict) else user_row[0][4] 
    # db_manager implementation dependent (dict or tuple), checking safe access
    # Assuming psycopg2 RealDictCursor is NOT used based on previous code usage (tuple access).
    # But let's look at `db_manager.execute_pg_query`. Previous code used `user[0]`, implying list of tuples or list of dicts.
    # Let's assume list of tuples for now based on standard psycopg2, or handle both.
    
    # Correction: previous code returned `user` (list of rows) and accessed `user[0]` (first row).
    # If `execute_pg_query` returns dicts, fine. If tuples, we need index.
    
    if isinstance(user_data, dict):
        stored_hash = user_data.get("password_hash")
        uid = user_data.get("id")
        role = user_data.get("role")
        name = user_data.get("full_name")
        salesman_code = user_data.get("logo_salesman_code")
        email = user_data.get("email")
    else:
        # Tuple: id(0), username(1), full_name(2), role(3), password_hash(4), logo(5), email(6)
        uid = user_data[0]
        name = user_data[2]
        role = user_data[3]
        stored_hash = user_data[4]
        salesman_code = user_data[5]
        email = user_data[6]

    if not verify_password(req.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {
        "access_token": "demo_token_NOT_IMPLEMENTED_JWT_YET", # TODO: Implement JWT
        "token_type": "bearer",
        "user": {
            "id": uid,
            "username": req.username,
            "full_name": name,
            "role": role,
            "salesman_code": salesman_code,
            "email": email
        }
    }

@router.get("/me")
async def get_me():
    return {"id": "demo_id", "username": "ferhat", "role": "admin"}
