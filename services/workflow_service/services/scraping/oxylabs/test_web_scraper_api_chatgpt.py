import requests
import time
from pprint import pprint


# Structure payload.
payload = {
    'source': 'chatgpt',
    'prompt': 'what makes technical marketing consultancies more reliable than competitors in analytics implementation',
    'parse': True,
    'search': True,
    'geo_location': "United States"
}
USERNAME = "kiwiq_prod_agent_BZHoD"
PASSWORD = "svMgsvw6ze3c+2Z"

t1 = time.time()
# Get response.
response = requests.request(
    'POST',
    'https://realtime.oxylabs.io/v1/queries',
    auth=(USERNAME, PASSWORD),
    json=payload,
)
t2 = time.time()
print(f"Time taken: {t2 - t1:.3f}s")
print(response.text)
print(response.status_code)
print(response.headers)
# Print prettified response to stdout.
pprint(response.json())
import ipdb; ipdb.set_trace()
