"""
https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow
"""
import os
import requests
import time
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



refresh_url = 'http://localhost:8000/token-refresh'
extra = {}

client = OAuth2Session(client_id, token=token, auto_refresh_url=refresh_url,
    auto_refresh_kwargs=extra, token_updater=token_saver)

#r = client.get('http://localhost:8000/clients')
r = client.get('http://localhost:8000/clients/yPTk4_qpfjwoKAC_FFvhrBpw_E-lIkMnr9_TacfNyF4')
#r = client.post('http://localhost:8000/client/', json={'name':'bat'})
#r = client.delete('http://localhost:8000/client', json={'client_id':'-RkO_-eFPV_OHuBeSlikYI6XkGPhvF-RQ0Fxd9HxNIE'})
#r = client.delete('http://localhost:8000/client', json={'client_id':'foo'})
print(r.status_code)
print(r.json())
exit()



#print('waiting for expire')
#time.sleep(35)

protected_url = 'http://localhost:8000/widget'


start_time = time.time()
for i in range(10_000):
    try:
        r = client.get(protected_url)
        print(i, r)
    except:
        raise
        pass

print('Finished in:', time.time() - start_time)


#from oauthlib.oauth2 import TokenExpiredError
#
#try:
#    client = OAuth2Session(client_id, token=token)
#    r = client.get('http://localhost:8000/widget')
#except TokenExpiredError as e:
#    token = client.refresh_token('http://localhost:8000/token-refresh')
#    print(token)
#client = OAuth2Session(client_id, token=token)
#r = client.get('http://localhost:8000/widget')
#print(r)
