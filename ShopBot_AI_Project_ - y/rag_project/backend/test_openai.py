#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API key and embedding functionality
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

def test_openai_api():
    # Load .env file
    load_env()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: No API key found in .env file!")
        return

    print(f"Testing API key: {api_key[:10]}...")
    print("Embedding model: text-embedding-3-small")

    try:
        client = OpenAI(api_key=api_key)

        # Test simple embedding
        print("Testing embedding API...")
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=["Hello world"]
        )

        print("SUCCESS: Embedding API works!")
        print(f"Embedding dimensions: {len(response.data[0].embedding)}")

    except Exception as e:
        print(f"ERROR: OpenAI API error: {e}")

if __name__ == "__main__":
    test_openai_api()