import requests
import json
import sys

response = requests.get("https://data.minorplanetcenter.net/api/query-identifier", data="C/2025 R3")

response.raise_for_status()
json.dump(response.json(), sys.stdout, indent=4)