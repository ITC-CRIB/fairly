from typing import Optional

import keyring

SERVICE_NAME = "fairly"

class KeyringUnavailableError(Exception):
    """Set the FAIRLY_ID_TOKEN environment variable to use the keyring."""
    pass

def set_token(id: str, token: str) -> None:
    """Set the token in the keyring."""
    try:
        keyring.set_password(SERVICE_NAME, id, token)
    except keyring.errors.KeyringError:
        raise KeyringUnavailableError(
            "Keyring is unavailable. Set the FAIRLY_ID_TOKEN environment variable instead."
        )

def get_token(id: str) -> Optional[str]:
    """Get the token from the keyring."""

    try:
        token = keyring.get_password(SERVICE_NAME, id)
    except keyring.errors.KeyringError:
        raise KeyringUnavailableError(
            "Keyring is unavailable. Set the FAIRLY_ID_TOKEN environment variable instead."
        )
    return token


def delete_token(id: str) -> None:
    """Delete the token from the keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, id)
    except keyring.errors.PasswordDeleteError:
        # Deleting a missing token should be a no-op.
        return
    except keyring.errors.KeyringError:
        raise KeyringUnavailableError(
            "Keyring is unavailable, thus tokens cannot be deleted"
        )

def resolve_token(id: str) -> Optional[list]:
    """Resolve the token from the keyring or environment variable."""
    token = get_token(id)
    if token is None:
        import os

        token = os.environ.get("FAIRLY_ID_TOKEN")
    return token