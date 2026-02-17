"""
GTM AI Operations Hub — Application Launcher
Run: python run.py
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env BEFORE importing the app
load_dotenv()

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "webapp.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
