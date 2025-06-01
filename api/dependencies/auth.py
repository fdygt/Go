from fastapi import Depends, HTTPException
from api.utils.security_utils import decode_token

# Contoh penggunaan dengan FastAPI OAuth2PasswordBearer
# from fastapi.security import OAuth2PasswordBearer
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str):  # Ganti dengan Depends(oauth2_scheme) jika pakai FastAPI
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
