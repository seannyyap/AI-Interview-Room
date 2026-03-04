import asyncio
import json
import websockets

async def test_ws():
    uri = "ws://localhost:8000/ws/audio"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected.")
            # receive ready
            res = await websocket.recv()
            print("Received:", res)
            
            # send start
            await websocket.send(json.dumps({
                "type": "interview-start",
                "config": {"position": "Engineer", "difficulty": "easy"}
            }))
            
            # Should receive interview_started
            res = await websocket.recv()
            print("Received:", res)
            
            # Should receive greeting text
            res = await websocket.recv()
            print("Received:", res)
            
            # Should receive TTS Audio chunk duration
            res = await websocket.recv()
            print("Received (TTS metadata):", res)
            
            # Wait for audio bytes
            audio_data = await websocket.recv()
            print(f"Received audio bytes: {len(audio_data)} bytes")
            
            # Send speech bytes to trigger response pipeline
            dummy_audio = bytes(16000 * 2) # 1 second of silence
            await websocket.send(dummy_audio)
            
            # Send speech-end
            await websocket.send(json.dumps({
                "type": "speech-end"
            }))
            
            print("Sent speech-end. Waiting for STT/Groq/TTS response...")
            start_time = asyncio.get_event_loop().time()
            while True:
                msg = await websocket.recv()
                elapsed = asyncio.get_event_loop().time() - start_time
                if isinstance(msg, bytes):
                    print(f"[{elapsed:.2f}s] Received audio bytes: {len(msg)}")
                else:
                    data = json.loads(msg)
                    typ = data.get("type")
                    if typ == "ai-response":
                        if data.get("is_complete"):
                            print(f"[{elapsed:.2f}s] AI RESPONSE COMPLETE.")
                            break
                        else:
                            # just print a dot for tokens to not flood console
                            print(".", end="", flush=True)
                    else:
                        print(f"\n[{elapsed:.2f}s] Received JSON: {typ} -> {msg}")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_ws())
