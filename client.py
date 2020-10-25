"""
https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow
"""
import os
from requests.auth import HTTPBasicAuth
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session




def token_saver(token):
    print(token)

#grab client_id and client_secret:
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
token_url = 'http://localhost:8000/token'

client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret, include_client_id=True)
print(token)

import time


print('waiting for expire')
time.sleep(35)

from oauthlib.oauth2 import TokenExpiredError

try:
    client = OAuth2Session(client_id, token=token)
    r = client.get('http://localhost:8000/widget')
except TokenExpiredError as e:
    token = client.refresh_token('http://localhost:8000/token-refresh')
    print(token)
client = OAuth2Session(client_id, token=token)
r = client.get('http://localhost:8000/widget')
print(r)
