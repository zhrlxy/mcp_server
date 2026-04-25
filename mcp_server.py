import asyncio
import json
import logging
from urllib.parse import parse_qs, urlparse
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed
import os

HOST = "0.0.0.0"
MCP_PATH = "/mcp/"
PORT = int(os.environ.get("PORT", "8765"))
EXPECTED_TOKEN = os.environ.get("MCP_TOKEN", "mcp_7f3c9a2e8b4d1f6a0c5e9d3b2a8f1c4e7d6b9a3c2f8e1d5a7b0c6e9f3d2a4b8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

TOOLS = [
    {
        "name": "who_is_james",
        "description": (
            "Use this tool when the user asks who James is, "
            "or asks about James, or explicitly asks you to use an external tool "
            "to identify James."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def make_result(session_id, request_id, result):
    return {
        "session_id": session_id,
        "type": "mcp",
        "payload": {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    }

def make_error(session_id, request_id, code, message):
    return {
        "session_id": session_id,
        "type": "mcp",
        "payload": {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    }


async def handle_mcp_message(websocket, raw_text):
    logging.info(f"RECV raw: {raw_text}")

    try:
        msg = json.loads(raw_text)
    except json.JSONDecodeError:
        response = make_error("", None, -32700, "Invalid JSON")
        await websocket.send(json.dumps(response, ensure_ascii=False))
        return
    
    if msg.get("type") == "hello":
        response = {
            "type": "hello",
            "version": msg.get("version", 3),
            "transport": "websocket",
            "features": {
                "mcp": True
            }
        }
        await websocket.send(json.dumps(response, ensure_ascii=False))
        logging.info(f"SEND hello response: {response}")
        return

    if msg.get("type") != "mcp":
        response = make_error("", None, -32600, "Unsupported message type")
        await websocket.send(json.dumps(response, ensure_ascii=False))
        return
    
    session_id = msg.get("session_id", "")
    payload = msg.get("payload", {})

    method = payload.get("method")
    request_id = payload.get("id")
    params = payload.get("params", {}) or {}

    logging.info(f"Parsed MCP method={method} id={str(request_id)} params={str(params)}")

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "james-mcp-server",
                "version": "1.0.0"
            }
        }
        response = make_result(session_id, request_id, result)
        await websocket.send(json.dumps(response, ensure_ascii=False))
        logging.info("SEND initialize result")
        return

    if method == "tools/list":
        result = {
            "tools": TOOLS
        }
        response = make_result(session_id, request_id, result)
        await websocket.send(json.dumps(response, ensure_ascii=False))
        logging.info("SEND tools/list result")
        return

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}

        logging.info(f"TOOL CALL name={tool_name} arguments={str(arguments)}")

        if tool_name != "who_is_james":
            response = make_error(
                session_id,
                request_id,
                -32601,
                f"Unknown tool: {tool_name}"
            )
            await websocket.send(json.dumps(response, ensure_ascii=False))
            return

        result = {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "James is Huanrong Zhang, who is the future star of Xiaozhi's product."
                        "This response comes from your external MCP server."
                    )
                }
            ]
        }
        response = make_result(session_id, request_id, result)
        await websocket.send(json.dumps(response, ensure_ascii=False))
        logging.info("SEND tools/call result")
        return

    response = make_error(session_id, request_id, -32601, f"Unknown method: {method}")
    await websocket.send(json.dumps(response, ensure_ascii=False))


async def ws_handler(websocket):
    request = websocket.request
    full_path = request.path  # e.g. /mcp/?token=demo-token

    parsed = urlparse(full_path)
    path = parsed.path
    token = parse_qs(parsed.query).get("token", [""])[0]

    logging.info(f"Incoming WS path={path} token={token}")

    if path != MCP_PATH:
        logging.info(f"Invalid path: {path}")
        await websocket.close(code=1008, reason="Invalid path")
        return

    if token != EXPECTED_TOKEN:
        logging.info("Invalid token")
        await websocket.close(code=1008, reason="Invalid token")
        return

    logging.info("Client connected")

    try:
        async for raw_text in websocket:
            await handle_mcp_message(websocket, raw_text)
    except ConnectionClosed:
        logging.info("Client disconnected")


async def main():
    logging.info(f"Starting MCP server at ws://{HOST}:{PORT}{MCP_PATH}?token={EXPECTED_TOKEN}")
    async with serve(ws_handler, HOST, PORT, max_size=8 * 1024 * 1024):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())