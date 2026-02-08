"""
Custom Telegram MCP Server - Direct API interaction.
Bypasses proxy issues by talking directly to api.telegram.org.
Optimized for use as a primary interface.
"""

import os
import asyncio
import httpx
import logging
import sys
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STATE_FILE = os.path.join(os.path.dirname(__file__), "tg_state.json")

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("telegram_mcp")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    return {"last_update_id": 0}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Error saving state: {e}")

logger.info(f"Server Startup - CHAT_ID: {repr(CHAT_ID)}")

mcp = FastMCP(
    name="Direct Telegram MCP",
    instructions="""
    Use this to communicate with the user via Telegram.
    1. 'interact_final_v5' sends a message and can optionally wait for a reply.
    2. 'poll_messages' is the primary way to wait for new messages (Pulsing Poll).
    3. 'get_messages' fetches recent history.
    """
)

@mcp.tool()
async def who_am_i() -> dict:
    """Return the script path and config status."""
    return {
        "file": __file__,
        "chat_id": CHAT_ID,
        "token_len": len(BOT_TOKEN),
        "state": load_state()
    }

@mcp.tool()
async def poll_messages(timeout: int = 100) -> dict:
    """
    Pulsing Poll: Wait for new messages for a specific duration (up to 120s).
    Use this in a loop to maintain a 'Wait-Notify' state.
    """
    state = load_state()
    last_id = state.get("last_update_id", 0)

    async with httpx.AsyncClient(timeout=timeout + 10) as client:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            "offset": last_id + 1,
            "timeout": timeout,
            "allowed_updates": ["message"]
        }
        
        try:
            res = await client.get(url, params=params)
            if res.status_code != 200:
                return {"status": "error", "message": res.text}
            
            updates = res.json().get("result", [])
            if not updates:
                return {"status": "timeout", "last_id": last_id}

            new_messages = []
            max_id = last_id
            for update in updates:
                max_id = max(max_id, update["update_id"])
                if "message" in update and str(update["message"]["chat"]["id"]) == str(CHAT_ID):
                    new_messages.append({
                        "text": update["message"].get("text", ""),
                        "from": update["message"].get("from", {}).get("username", "unknown"),
                        "date": update["message"].get("date")
                    })
            
            state["last_update_id"] = max_id
            save_state(state)
            
            if new_messages:
                return {"status": "received", "messages": new_messages}
            else:
                return {"status": "timeout", "last_id": max_id}

        except Exception as e:
            return {"status": "error", "message": str(e)}

@mcp.tool()
async def interact_final_v5(
    project_name: str,
    session_name: str,
    message: str | None = None,
    wait_for_reply: bool = False,
    choices: list[str] | None = None,
) -> dict:
    """
    Send a message and optionally wait for a reply using the stateful system.
    """
    if not BOT_TOKEN or not CHAT_ID:
        return {"error": "BOT_TOKEN or CHAT_ID not set"}

    formatted_msg = f"[{project_name} | {session_name}]\n{message if message else ''}"
    
    async with httpx.AsyncClient(timeout=120) as client:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": formatted_msg}
        if choices:
            keyboard = [[{"text": c}] for c in choices]
            payload["reply_markup"] = {"keyboard": keyboard, "one_time_keyboard": True}

        send_res = await client.post(url, json=payload)
        if send_res.status_code != 200:
            return {"error": f"Send API Error: {send_res.text}"}
        
        if wait_for_reply:
            # Use poll_messages logic for a single wait
            reply = await poll_messages(timeout=60)
            return reply
        
        return {"status": "sent", "response": send_res.json()}

@mcp.tool()
async def get_messages(limit: int = 10) -> dict:
    """Get recent history from the direct chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"limit": 100, "allowed_updates": ["message"]})
        if response.status_code != 200:
            return {"error": f"API Error: {response.text}"}
        
        updates = response.json().get("result", [])
        relevant = []
        for u in reversed(updates):
            if "message" in u and str(u["message"]["chat"]["id"]) == str(CHAT_ID):
                relevant.append({
                    "text": u["message"].get("text", ""),
                    "from": u["message"].get("from", {}).get("username", "unknown"),
                    "date": u["message"].get("date")
                })
                if len(relevant) >= limit: break
        return {"messages": relevant}

if __name__ == "__main__":
    mcp.run()
