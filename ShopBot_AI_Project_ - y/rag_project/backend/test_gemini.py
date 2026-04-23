#!/usr/bin/env python3
"""
Test Google Gemini API
"""
import os
import google.genai as genai

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

def test_gemini_api():
    load_env()
    api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key or api_key == "your-gemini-api-key-here":
        print("ERROR: No Gemini API key found in .env file!")
        print("Please add GEMINI_API_KEY=your_key_here to the .env file")
        print("Get key from: https://makersuite.google.com/app/apikey")
        return

    print(f"Testing Gemini API key: {api_key[:10]}...")

    try:
        client = genai.Client(api_key=api_key)

        # Explore API structure
        print("Available attributes in genai module:")
        print([attr for attr in dir(genai) if not attr.startswith('_')])

        print("Available methods in client:")
        print([attr for attr in dir(client) if not attr.startswith('_')])

        print("Available methods in client.models:")
        print([attr for attr in dir(client.models) if not attr.startswith('_')])

        # List available models first
        print("Listing available models...")
        models = client.models.list()
        for model in models:
            if 'embed' in model.name.lower():
                print(f"Available embedding model: {model.name}")

        # Try embedding with available model
        print("Testing Gemini embeddings...")
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents="Hello world"
            )
            print("SUCCESS: Embeddings work!")
            print(f"Result type: {type(result)}")
            print(f"Embedding length: {len(result.embeddings[0].values)}")
        except Exception as e2:
            print(f"Embedding test failed: {e2}")

            # Try different embedding model
            try:
                result = client.models.embed_content(
                    model="gemini-embedding-2",
                    contents="Hello world"
                )
                print("SUCCESS: Embeddings work with gemini-embedding-2!")
                print(f"Result type: {type(result)}")
            except Exception as e3:
                print(f"gemini-embedding-2 also failed: {e3}")

        # Check all models and their supported methods
        print("Checking all available models and methods...")
        for model in models:
            if 'gemini' in model.name.lower() and 'pro' in model.name.lower():
                print(f"Model: {model.name}")
                break

        # Try common Gemini models
        common_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
        for model_name in common_models:
            try:
                print(f"Testing {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents="Hello, test message"
                )
                print(f"SUCCESS: {model_name} works!")
                print(f"Response: {response.candidates[0].content.parts[0].text[:50]}...")
                break
            except Exception as e:
                print(f"{model_name} failed: {str(e)[:50]}...")
                continue

    except Exception as e:
        print(f"ERROR: Gemini API error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_api()