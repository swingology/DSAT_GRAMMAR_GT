"""Google Sign-In ID token verification.

Isolated behind a single function so tests can fake the network-dependent
verification at its seam. The client secret is never used: Google ID tokens are
verified against Google's public signing keys.
"""

import logging

from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import get_settings

logger = logging.getLogger(__name__)

_ALLOWED_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


class GoogleTokenError(Exception):
    """Raised when a Google credential fails verification."""


def verify_google_id_token(credential: str) -> dict:
    """Verify a Google ID token and return its claims.

    Checks signature, audience (our client ID), and expiry via google-auth, then
    additionally pins the issuer and requires a verified email.

    Raises GoogleTokenError on any verification failure.
    """
    settings = get_settings()
    try:
        claims = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.google_oauth_client_id,
        )
    except (ValueError, GoogleAuthError) as exc:
        raise GoogleTokenError(str(exc)) from exc

    if claims.get("iss") not in _ALLOWED_ISSUERS:
        raise GoogleTokenError(f"Untrusted issuer: {claims.get('iss')!r}")

    if not claims.get("email"):
        raise GoogleTokenError("Token contains no email claim")

    # A Google account can carry an unverified email; treating it as an identity
    # would let someone claim a registered student's address.
    if not claims.get("email_verified"):
        raise GoogleTokenError("Email is not verified by Google")

    return claims
