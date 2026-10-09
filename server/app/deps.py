import secrets

from fastapi import Depends, Header, HTTPException, Query, status

from app.config import Settings, get_settings


def token_matches(provided: str | None, settings: Settings) -> bool:
    expected = settings.api_pairing_token
    return not expected or (provided is not None and secrets.compare_digest(provided, expected))


def require_token(
    x_pairing_token: str | None = Header(default=None),
    token: str | None = Query(default=None, description="Alternative to the header, for media URLs"),
    settings: Settings = Depends(get_settings),
) -> None:
    """When API_PAIRING_TOKEN is set, every request must carry it."""
    if not token_matches(x_pairing_token or token, settings):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or wrong pairing token")
