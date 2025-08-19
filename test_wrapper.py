#!/usr/bin/env python3
"""
Test script for the AutoGen API Bridge
Run this to test your API bridge independently of Open WebUI
"""

import asyncio
import aiohttp
import json
import sys

async def test_non_streaming():
    """Test non-streaming chat completion"""
    print("Testing non-streaming completion...")
    
    payload = {
        "model": "autogen-system",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
                    if "choices" in result and result["choices"]:
                        content = result["choices"][0]["message"]["content"]
                        print(f"\nExtracted content: {content}")
                    else:
                        print("No choices found in response")
                else:
                    text = await response.text()
                    print(f"Error response: {text}")
                    
        except Exception as e:
            print(f"Error: {e}")

async def test_streaming():
    """Test streaming chat completion"""
    print("\nTesting streaming completion...")
    
    payload = {
        "model": "autogen-system",
        "messages": [
            {"role": "user", "content": "Tell me a short story"}
        ],
        "stream": True
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    print("Streaming response:")
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            print(f"Raw line: {repr(line)}")
                            if line.startswith("data: "):
                                data_part = line[6:]  # Remove "data: " prefix
                                if data_part == "[DONE]":
                                    print("Stream completed")
                                    break
                                try:
                                    chunk = json.loads(data_part)
                                    if "choices" in chunk and chunk["choices"]:
                                        delta = chunk["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            print(f"Content chunk: {delta['content']}")
                                except json.JSONDecodeError:
                                    print(f"Failed to parse JSON: {data_part}")
                else:
                    text = await response.text()
                    print(f"Error response: {text}")
                    
        except Exception as e:
            print(f"Error: {e}")

async def test_models_endpoint():
    """Test the models endpoint"""
    print("\nTesting models endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/v1/models") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"Models: {json.dumps(result, indent=2)}")
                else:
                    text = await response.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Error: {e}")

async def test_health_endpoint():
    """Test the health endpoint"""
    print("\nTesting health endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/health") as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"Health: {json.dumps(result, indent=2)}")
                else:
                    text = await response.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Error: {e}")

def test_with_curl():
    """Print curl commands for manual testing"""
    print("\n" + "="*50)
    print("Manual testing with curl:")
    print("="*50)
    
    print("\n1. Test models endpoint:")
    print("curl -X GET http://localhost:8000/v1/models")
    
    print("\n2. Test non-streaming completion:")
    print('''curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "autogen-system",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }' ''')
    
    print("\n3. Test streaming completion:")
    print('''curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "autogen-system",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }' ''')

async def main():
    """Run all tests"""
    print("AutoGen API Bridge Test Suite")
    print("="*40)
    
    # Test basic endpoints first
    await test_health_endpoint()
    await test_models_endpoint()
    
    # Test chat completions
    await test_non_streaming()
    await test_streaming()
    
    # Print manual testing commands
    test_with_curl()
    
    print(f"\nIf you see this message, the server is responding.")
    print("Check the server logs for any error messages.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)