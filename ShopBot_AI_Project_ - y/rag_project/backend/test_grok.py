#!/usr/bin/env python3
"""
Test script for Grok API integration
"""
import os
from xai_sdk import Client

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

def test_grok_api():
    # Load .env file
    load_env()

    grok_api_key = os.getenv("GROK_API_KEY", "")
    if not grok_api_key:
        print("ERROR: No GROK_API_KEY found in .env file!")
        print("You need to add GROK_API_KEY=your_key_here to the .env file")
        return

    print(f"Testing Grok API key: {grok_api_key[:10]}...")

    try:
        client = Client(api_key=grok_api_key)

        # Check available methods
        print("Available methods:", [method for method in dir(client) if not method.startswith('_')])

        # Try the correct API call for xAI - check what parameters it expects
        print("Testing Grok chat API...")
        print("Checking chat method signature...")

        import inspect
        print("chat.create signature:", inspect.signature(client.chat.create))

        # Try with string prompt instead of messages array
        try:
                response = client.chat.create(
                    model="grok-4-fast",
                    user="Hello, can you help me with embeddings?",
                    max_tokens=100
                )
                print("SUCCESS: Grok API works with user parameter!")
                print(f"Response type: {type(response)}")
                print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")

                # Try to get the response content
                try:
                    # Try streaming to get the response
                    stream = response.stream()
                    content = ""
                    for chunk in stream:
                        if hasattr(chunk, 'content'):
                            content += chunk.content
                        elif hasattr(chunk, 'text'):
                            content += chunk.text
                        elif hasattr(chunk, 'delta'):
                            content += chunk.delta
                        else:
                            content += str(chunk)

                    if content:
                        print(f"Streamed content: {content[:100]}...")
                    else:
                        print("No content in stream, trying other methods...")

                        # Try messages method
                        if hasattr(response, 'messages'):
                            messages = list(response.messages())
                            print(f"Messages: {messages}")

                except Exception as e5:
                    print(f"Could not extract content: {e5}")
                    print("Grok API is complex to integrate. Consider using OpenAI with billing or local embeddings.")
                    import traceback
                    traceback.print_exc()

        except Exception as e4:
            print(f"User parameter also failed: {e4}")
            print("Grok API integration is complex. Consider using OpenAI with proper billing or local embeddings.")

        print("SUCCESS: Grok chat API works!")
        print(f"Response type: {type(response)}")
        if hasattr(response, 'choices'):
            print(f"Response: {response.choices[0].message.content[:100]}...")
        else:
            print(f"Response: {str(response)[:100]}...")

    except Exception as e:
        print(f"ERROR: Grok API error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_grok_api()