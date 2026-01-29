#!/usr/bin/env python3
"""
Direct test of ticket processing via API
"""

import asyncio
import json
import httpx
from pathlib import Path
import tempfile

async def main():
    base_url = "http://localhost:8002"
    
    # Load sample tickets
    tickets_file = Path("data/sample_tickets.json")
    with open(tickets_file) as f:
        data = json.load(f)
    
    tickets = data["tickets"][:3]  # First 3 tickets
    print(f"\nTesting {len(tickets)} tickets via API...\n")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Check health
        resp = await client.get(f"{base_url}/api/health")
        print(f"Backend health: {resp.status_code}")
        
        # Check skills
        resp = await client.get(f"{base_url}/api/skills/")
        if resp.status_code == 200:
            data = resp.json()
            skills = data.get("skills", [])
            print(f"Available skills: {len(skills)}")
            for skill in skills:
                print(f"  - {skill.get('name', 'unknown')}")
        
        # Upload tickets as a file
        print(f"\nUploading {len(tickets)} tickets:")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"tickets": tickets}, f)
            temp_file = f.name
        
        try:
            with open(temp_file, 'rb') as f:
                files = {'file': ('tickets.json', f, 'application/json')}
                resp = await client.post(f"{base_url}/api/tickets/upload", files=files)
            
            if resp.status_code == 200:
                result = resp.json()
                run_id = result.get("run_id")
                print(f"Upload successful - Run ID: {run_id}")
                
                # Process the tickets
                print(f"\nProcessing tickets (this may take a minute or two)...")
                try:
                    resp = await client.post(f"{base_url}/api/tickets/process/{run_id}")
                    if resp.status_code == 200:
                        result = resp.json()
                        print(f"Processing complete!")
                        print(f"  - Processed: {result.get('processed_tickets')} tickets")
                        print(f"  - Proposed skills: {result.get('proposed_skills')}")
                    else:
                        print(f"Processing failed: {resp.status_code}")
                        try:
                            print(resp.json())
                        except:
                            print(resp.text)
                except Exception as e:
                    print(f"Error during processing: {e}")
                    print("(This can happen if Ollama is slow - checking proposed skills anyway)")
            else:
                print(f"Upload failed: {resp.status_code}")
                print(resp.text)
        finally:
            Path(temp_file).unlink()
        
        # Check proposed skills
        print(f"\nChecking proposed skills...")
        resp = await client.get(f"{base_url}/api/skills/proposed")
        if resp.status_code == 200:
            data = resp.json()
            proposed = data.get("skills", [])
            count = data.get("count", 0)
            print(f"Proposed skills: {count}")
            for skill in proposed:
                if isinstance(skill, dict):
                    print(f"  - {skill.get('name', 'unknown')} ({skill.get('status', 'unknown')})")
                else:
                    print(f"  - {skill}")
        else:
            print(f"Failed to get proposed skills: {resp.status_code}")
    
    print("\nDone!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
