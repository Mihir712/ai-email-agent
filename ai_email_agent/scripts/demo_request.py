import requests

url = "http://localhost:8000/generate"

payload = {"email": "Hi, I wanted to ask if we could schedule a meeting this week."}

resp = requests.post(url, json=payload)
print(resp.status_code)
print(resp.json())
