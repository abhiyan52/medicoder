import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    FastAPI dependency that enforces HTTP Basic Auth.

    Uses constant-time comparison (secrets.compare_digest) to prevent
    timing attacks where an attacker could guess the password character
    by character based on how long the comparison takes.

    Returns the verified username on success, raises 401 on failure.
    """
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.API_USERNAME.encode("utf-8"),
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.API_PASSWORD.encode("utf-8"),
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},  # Tells the browser to show a login prompt
        )

    return credentials.username
