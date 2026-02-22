import requests

url = "https://api-bcbe5a.stack.tryrelevance.com/latest/agents/trigger"
headers = {
    "Authorization": "12bdbde1-399a-4bba-9955-304cebce6cad:sk-Y2YxZjc0MGEtYjViMy00Zjc2LTljNGItYzU3ZTY5NmUzZDNm",
    "Content-Type": "application/json"
}
payload = {
    "message": {"role": "user", "content": "Hello"},
    "agent_id": "f6824156-1540-41bb-853c-d22aab2cc075"
}

resp = requests.post(url, headers=headers, json=payload)
print(resp.status_code)
print(resp.json())
