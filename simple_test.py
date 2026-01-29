#!/usr/bin/env python3
"""
Minimal API test - just check if server responds
"""

import asyncio
import httpx
import json
from pathlib import Path


async def test_health():
    """Test health endpoint"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("Testing /api/health...")
            resp = await client.get("http://localhost:8002/api/health")
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.json()}")
            return True
    except Exception as e:
        print(f"Failed: {e}")
        return False


async def main():
    await test_health()


if __name__ == "__main__":
    asyncio.run(main())
