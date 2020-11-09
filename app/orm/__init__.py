"""
The secrets module gives Base64 encoded text which is ~1.3 characters per byte.

For details on use of the secrets module for cryptographic key generation see:
https://docs.python.org/3/library/secrets.html
"""
OAUTH2_CLIENT_ID_BYTES = 32
OAUTH2_CLIENT_SECRET_BYTES = 64
OAUTH2_ACCESS_TOKEN_BYTES = 32
OAUTH2_REFRESH_TOKEN_BYTES = 64

OAUTH2_CLIENT_ID_MAX_CHARS = int(OAUTH2_CLIENT_ID_BYTES * 1.5)
OAUTH2_CLIENT_SECRET_MAX_CHARS = int(OAUTH2_CLIENT_SECRET_BYTES * 1.5)
OAUTH2_ACCESS_TOKEN_MAX_CHARS = int(OAUTH2_ACCESS_TOKEN_BYTES * 1.5)
OAUTH2_REFRESH_TOKEN_MAX_CHARS = int(OAUTH2_REFRESH_TOKEN_BYTES * 1.5)
