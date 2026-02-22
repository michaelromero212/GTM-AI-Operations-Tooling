"""
Relevance AI Agent Handler
Supports triggering specialized GTM research agents and checking connectivity.
"""
import os
import requests
from typing import Optional, Dict, Any

class RelevanceAgentHandler:
    """
    Handler for Relevance AI Workforce integration.
    """
    def __init__(self):
        self.project_id = os.getenv("RELEVANCE_PROJECT_ID")
        self.api_key = os.getenv("RELEVANCE_API_KEY")
        self.agent_id = os.getenv("RELEVANCE_AGENT_ID")
        self.region = os.getenv("RELEVANCE_REGION", "us-east-1")
        
        # Relevance AI API endpoints
        # Support both standard regions and custom stack URLs
        if ".stack.tryrelevance.com" in self.region:
            self.base_url = f"https://{self.region}/latest"
        else:
            self.base_url = f"https://api.{self.region}.relevance.ai/v1"
            
        self.headers = {
            "Authorization": f"{self.project_id}:{self.api_key}",
            "Content-Type": "application/json"
        }

    def trigger_research(self, company_name: str, context: str = "") -> Dict[str, Any]:
        """
        Trigger the Relevance AI agent to perform deep research.
        """
        if not all([self.project_id, self.api_key, self.agent_id]):
            return {"status": "error", "message": "Relevance AI credentials missing"}

        url = f"{self.base_url}/agents/trigger"
        payload = {
            "agent_id": self.agent_id,
            "message": {
                "role": "user",
                "content": f"Perform deep GTM research for {company_name}. Context: {context}"
            }
        }

        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "success",
                    "conversation_id": data.get("conversation_id"),
                    "message": "Research agent triggered successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API Error {resp.status_code}: {resp.text[:100]}"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_health(self) -> Dict[str, Any]:
        """
        Check if Relevance AI integration is configured and responsive.
        """
        if not all([self.project_id, self.api_key, self.agent_id]):
            return {"status": "unconfigured", "message": "Missing Agent ID or API Key"}
        
        # Use agents list as a general connectivity check
        url = f"{self.base_url}/agents/list"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return {"status": "connected", "message": "Relevance AI Online"}
            else:
                return {"status": "error", "message": f"Auth failed ({resp.status_code})"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def chat_with_agent(self, agent_id: str, message: str) -> Dict[str, Any]:
        """
        Send a generic chat message to a specific Relevance AI agent and poll for the answer.
        """
        if not all([self.project_id, self.api_key]):
            return {"status": "error", "message": "Relevance AI credentials missing"}

        url = f"{self.base_url}/agents/trigger"
        payload = {
            "agent_id": agent_id,
            "message": {
                "role": "user",
                "content": message
            }
        }

        headers = {
            "Authorization": f"{self.project_id}:{self.api_key}",
            "Content-Type": "application/json"
        }

        import time

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                
                job_info = data.get("job_info", {})
                job_id = job_info.get("job_id")
                studio_id = job_info.get("studio_id")
                
                if job_id and studio_id:
                    poll_url = f"{self.base_url}/studios/{studio_id}/async_poll/{job_id}"
                    
                    # Poll for up to 60 seconds
                    for _ in range(30):
                        time.sleep(2)
                        p_resp = requests.get(poll_url, headers=headers, timeout=30)
                        if p_resp.status_code == 200:
                            p_data = p_resp.json()
                            updates = p_data.get("updates", [])
                            
                            # Search backwards for the final answer
                            for update in reversed(updates):
                                if update.get("type") in ["chain-success", "agent-step"]:
                                    out = update.get("output", {})
                                    # Output might be nested or direct
                                    if "answer" in out:
                                        return {"status": "success", "response": {"output": out["answer"]}}
                                    if "text" in out:
                                        return {"status": "success", "response": {"output": out["text"]}}
                                    if isinstance(out.get("output"), dict) and "answer" in out["output"]:
                                        return {"status": "success", "response": {"output": out["output"]["answer"]}}
                            
                            # check if job failed
                            if any(u.get("type") == "chain-failed" for u in updates):
                                return {"status": "error", "message": "Agent execution failed."}
                                
                    return {"status": "error", "message": "Timed out waiting for agent response."}
                    
                # Fallback if no async job mapping
                return {"status": "success", "response": data}
            else:
                return {
                    "status": "error",
                    "message": f"API Error {resp.status_code}: {resp.text[:100]}"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
