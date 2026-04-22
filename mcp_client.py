import asyncio
import json
import uuid
import websockets

WS_URL = "ws://127.0.0.1:8765/mcp/?token=mcp_7f3c9a2e8b4d1f6a0c5e9d3b2a8f1c4e7d6b9a3c2f8e1d5a7b0c6e9f3d2a4b8"
SESSION_ID = str(uuid.uuid4())


async def send_and_recv(ws, payload):
    msg = {
        "session_id": SESSION_ID,
        "type": "mcp",
        "payload": payload,
    }
    text = json.dumps(msg, ensure_ascii=False)
    print(f"\n>>> SEND\n{text}")
    await ws.send(text)

    resp = await ws.recv()
    print(f"<<< RECV\n{resp}")
    return json.loads(resp)


async def main():
    async with websockets.connect(WS_URL, max_size=8 * 1024 * 1024) as ws:
        #initialize
        await send_and_recv(ws, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "local-mcp-test-client",
                    "version": "1.0.0"
                }
            }
        })

        #tools/list
        await send_and_recv(ws, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })

        #tools/call
        await send_and_recv(ws, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "who_is_james",
                "arguments": {}
            }
        })


if __name__ == "__main__":
    asyncio.run(main())