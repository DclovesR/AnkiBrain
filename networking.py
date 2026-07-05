import os.path

import httpx
from aqt import mw

_clients: dict[bool, httpx.AsyncClient] = {}


# TODO

#Check enviornment mode:

def is_prod_env():
    return not is_dev_env()


def is_dev_env():
    return mw.settingsManager.settings['devMode']


def _is_tls_verification_enabled() -> bool:
    return not is_dev_env()


async def _get_client(verify_tls: bool) -> httpx.AsyncClient:
    client = _clients.get(verify_tls)
    if client is None:
        client = httpx.AsyncClient(
            timeout=60,
            verify=verify_tls,
            headers={'Content-Type': 'application/json'}
        )
        _clients[verify_tls] = client

    return client


async def close_http_clients():
    for client in _clients.values():
        await client.aclose()

    _clients.clear()


#Define function "fetch" which performs different HTTP requests (GET, POST, DELETE) asynchronously. POST function uses JSON format, 
#all responses return in JSON

async def fetch(url, verb, data):
    try:
        client = await _get_client(_is_tls_verification_enabled())
        verb_lower = verb.lower()

        if verb_lower == 'get':
            res = await client.get(url, params=data)
        elif verb_lower == 'post':
            res = await client.post(url, json=data)
        elif verb_lower == 'delete':
            res = await client.delete(url, params=data)
        else:
            raise ValueError(f'Unsupported HTTP verb: {verb_lower}')

        #res.raise_for_status() #raises error for HTTP status codes (ex. 4xx or 5xx)
        #print(res)
        return res.json()
    except Exception as exc:
        print(exc)
        raise exc

#The function "postDocument" reads in a document as binary data then uploads that data to a specified URL using a POST request.
#Response is returned as JSON. 

async def postDocument(file_path: str, url, accessToken: str):
    headers = {'Authorization': f'Bearer {accessToken}'}
    filename = os.path.basename(file_path)

    with open(file_path, 'rb') as f:
        file_data = f.read()

    files = {'file': (filename, file_data)}

    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=3600, pool=3600, read=3600, write=3600)) as client:
        res = await client.post(url, headers=headers, files=files)
        res.raise_for_status() 
        res = res.json()
        return res