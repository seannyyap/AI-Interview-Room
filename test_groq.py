import asyncio
import os
import sys

# Ensure backend config can load
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.providers.groq_llm import GroqLLMProvider

async def main():
    print("Testing Groq...")
    provider = GroqLLMProvider()
    await provider.load()
    if not provider.is_ready():
        print("Provider not ready!")
        return
        
    messages = [{"role": "user", "content": "Hello! Reply with a single sentence."}]
    print("Sending request...")
    
    count = 0
    async for token in provider.generate(messages):
        print(f"TOKEN: {token}")
        count += 1
        
    print(f"Total tokens: {count}")

if __name__ == "__main__":
    asyncio.run(main())
