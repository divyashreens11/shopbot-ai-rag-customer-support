#!/usr/bin/env python3
"""
Test OpenAI API key status
"""
import os
from openai import OpenAI

def load_env():
    """Load environment variables from .env file"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

def test_api_key():
    load_env()
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        print("❌ No API key found")
        return

    print(f"Testing API key: {api_key[:10]}...")

    try:
        client = OpenAI(api_key=api_key)

        # Test embedding (costs very little)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=["test"]
        )
        print("SUCCESS: API key works! Embeddings available.")
        print(f"Embedding dimensions: {len(response.data[0].embedding)}")

    except Exception as e:
        if "insufficient_quota" in str(e):
            print("ERROR: API key has insufficient quota/billing")
            print("SOLUTION: Add payment method to your OpenAI account")
            print("Go to: https://platform.openai.com/account/billing")
            print("Add a credit card and set up billing")
        else:
            print(f"API error: {e}")

if __name__ == "__main__":
    test_api_key()