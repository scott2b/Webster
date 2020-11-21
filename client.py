"""
https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow
"""
import os
import requests
import time
from requests.auth import HTTPBasicAuth
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from requests_oauthlib import OAuth2Session


def token_saver(token):
    print(token)

#grab client_id and client_secret:
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
token_url = 'http://localhost:8000/v1/token'


#def raise_on_error(response):
#    response.raise_for_status()
#    return response


client = BackendApplicationClient(client_id=client_id)
#client.register_compliance_hook('access_token_response', raise_on_error)
oauth = OAuth2Session(client=client)




try:
    token = oauth.fetch_token(token_url=token_url, client_id=client_id,
        client_secret=client_secret, include_client_id=True)
except MissingTokenError:
    # oauthlib gives this stupid error regardless of the problem
    print('Something went wrong, please check your client credentials.')
    exit()
print(token)

# time.sleep(30)

refresh_url = 'http://localhost:8000/v1/token-refresh'
extra = {}

client = OAuth2Session(client_id, token=token, auto_refresh_url=refresh_url,
    auto_refresh_kwargs=extra, token_updater=token_saver)


print('GETTING USER PROFILE')
r = client.get('http://localhost:8000/v1/profile')
print(r.status_code)
print(r.json())

print('UPDATING USER PROFILE')
data = r.json()
data['full_name'] += 'x'
data['password'] = 'foo'
data['hashed_password'] = 'foo'
data['is_superuser'] = True
r = client.put('http://localhost:8000/v1/profile', json=data)
print(r.status_code)
print(r.json())

print('CHANGING USER PASSWORD')
data = { 'password': 'scott' }
r = client.put('http://localhost:8000/v1/password', json=data)
print(r.status_code)
print(r.json())


#print('ATTEMPT TO SET HASH DIRECTLY')
#data = { 'hashed_password': 'foo' }
#r = client.put('http://localhost:8000/v1/password', json=data)
#print(r.status_code)
##print(r.json())



# Get the list of clients
r = client.get('http://localhost:8000/v1/clients')
print(r.status_code)
print(r.json())

print('CREATING A CLIENT')
r = client.post('http://localhost:8000/v1/clients', json={'name':'bat'})
print(r.status_code)
print(r.json())
#new_client_id = r.json()['client_id']

#print('Created new client:', new_client_id)
#print('Now getting')
#r = client.get(f'http://localhost:8000/v1/clients/{new_client_id}')
#print(r.status_code)
#print(r.json())

#print('Now deleting:')
#r = client.delete(f'http://localhost:8000/v1/clients/{new_client_id}')
#print(r.status_code)
#print(r.json())

#r = client.get('http://localhost:8000/clients')
#r = client.get('http://localhost:8000/v1/clients/yPTk4_qpfjwoKAC_FFvhrBpw_E-lIkMnr9_TacfNyF4')
#r = client.post('http://localhost:8000/client/', json={'name':'bat'})
#r = client.delete('http://localhost:8000/client', json={'client_id':'-RkO_-eFPV_OHuBeSlikYI6XkGPhvF-RQ0Fxd9HxNIE'})
#r = client.delete('http://localhost:8000/client', json={'client_id':'foo'})
#print(r.status_code)
#print(r.json())



#print('waiting for expire')
#time.sleep(35)

protected_url = 'http://localhost:8000/v1/profile'


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
