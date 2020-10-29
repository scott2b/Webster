"""
The secrets module gives Base64 encoded text which is ~1.3 characters per byte.

For details on use of the secrets module for cryptographic key generation see:
https://docs.python.org/3/library/secrets.html
"""
CLIENT_ID_BYTES = 32
CLIENT_SECRET_BYTES = 64
ACCESS_TOKEN_BYTES = 32
REFRESH_TOKEN_BYTES = 64

CLIENT_ID_MAX_CHARS = int(CLIENT_ID_BYTES * 1.5)
CLIENT_SECRET_MAX_CHARS = int(CLIENT_SECRET_BYTES * 1.5)
ACCESS_TOKEN_MAX_CHARS = int(ACCESS_TOKEN_BYTES * 1.5)
REFRESH_TOKEN_MAX_CHARS = int(REFRESH_TOKEN_BYTES * 1.5)
