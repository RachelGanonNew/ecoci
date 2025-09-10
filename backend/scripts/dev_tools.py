"""
Development tools for testing without webhooks.
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def load_fixture(event_type: str) -> Dict[str, Any]:
    """Load a GitHub webhook event fixture."""
    fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "github_events"
    fixture_path = fixtures_dir / f"{event_type}.json"
    
    if not fixture_path.exists():
        available = [f.stem for f in fixtures_dir.glob("*.json")]
        raise ValueError(
            f"No fixture found for {event_type}. "
            f"Available fixtures: {', '.join(available)}"
        )
    
    with open(fixture_path, 'r') as f:
        return json.load(f)

async def trigger_event(event_type: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Trigger a GitHub webhook event."""
    if payload is None:
        payload = load_fixture(event_type)
    
    headers = {
        "X-GitHub-Event": event_type,
        "Content-Type": "application/json",
    }
    
    # In development mode, use the direct endpoint
    url = f"{BASE_URL}/api/dev/trigger-event"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    
    return {
        "status": response.status_code,
        "data": response.json()
    }

async def main():
    """Run the development tools."""
    print("Available commands:")
    print("1. Trigger push event")
    print("2. Trigger pull request event")
    print("3. List available events")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        result = await trigger_event("push")
    elif choice == "2":
        result = await trigger_event("pull_request")
    elif choice == "3":
        fixtures_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "github_events"
        events = [f.stem for f in fixtures_dir.glob("*.json")]
        print("\nAvailable events:")
        for event in events:
            print(f"- {event}")
        return
    else:
        print("Invalid choice")
        return
    
    print("\nResponse:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
