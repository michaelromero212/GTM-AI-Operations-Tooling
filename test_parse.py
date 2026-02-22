import requests
import json
import time

url = "https://api-bcbe5a.stack.tryrelevance.com/latest/agents/trigger"
headers = {
    "Authorization": "12bdbde1-399a-4bba-9955-304cebce6cad:sk-Y2YxZjc0MGEtYjViMy00Zjc2LTljNGItYzU3ZTY5NmUzZDNm",
    "Content-Type": "application/json"
}
payload = {
    "message": {"role": "user", "content": "Hello!"},
    "agent_id": "f6824156-1540-41bb-853c-d22aab2cc075"
}

resp = requests.post(url, headers=headers, json=payload).json()
job_info = resp.get("job_info", {})
job_id = job_info.get("job_id")
studio_id = job_info.get("studio_id")

poll_url = f"https://api-bcbe5a.stack.tryrelevance.com/latest/studios/{studio_id}/async_poll/{job_id}"
while True:
    time.sleep(2)
    poll_resp = requests.get(poll_url, headers=headers).json()
    updates = poll_resp.get("updates", [])
    if any(u.get("type") in ["chain-success", "chain-failed"] for u in updates):
        for update in updates:
            if update.get("type") == "chain-success":
                print("OUTPUT:")
                print(json.dumps(update.get("output"), indent=2))
        break
