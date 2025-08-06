from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.web_service.auth import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    # Here you would typically fetch the user from your database based on payload data
    # For now, we'll just return the payload
    return payload
