#!/usr/bin/env python3
"""
Simple test of the ITSM agent with fixed self-learning
"""

import asyncio
import json
from pathlib import Path
from backend.models import Ticket
from backend.services.ticket_processor import ticket_processor
from backend.services.learning_engine import learning_engine

async def main():
    # Load sample tickets
    tickets_file = Path("data/sample_tickets.json")
    with open(tickets_file) as f:
        data = json.load(f)
    
    tickets = [Ticket(**t) for t in data["tickets"]]
    print(f"Loaded {len(tickets)} tickets\n")
    
    # Process all tickets
    print("=" * 70)
    print("PROCESSING TICKETS")
    print("=" * 70)
    
    results = []
    success_count = 0
    
    for i, ticket in enumerate(tickets, 1):
        result = await ticket_processor.process_ticket(ticket)
        results.append(result)
        
        # Check if routing was correct
        routing_correct = result.routing_correct if result.routing_correct is not None else False
        status = "[OK]" if routing_correct else "[FAIL]"
        if routing_correct:
            success_count += 1
        
        print(f"{i:2d}. {status} {ticket.id}: {ticket.title[:40]}")
        print(f"     Predicted: {result.prediction.predicted_routing}")
        print(f"     Actual:    {ticket.actual_routing}")
    
    # Summary
    print("\n" + "=" * 70)
    print("ACCURACY SUMMARY")
    print("=" * 70)
    
    category_correct = sum(1 for r in results if r.category_correct)
    routing_correct = sum(1 for r in results if r.routing_correct)
    resolution_correct = sum(1 for r in results if r.resolution_correct)
    
    print(f"Category:  {category_correct}/{len(results)} ({100*category_correct//len(results)}%)")
    print(f"Routing:   {routing_correct}/{len(results)} ({100*routing_correct//len(results)}%)")
    print(f"Resolution: {resolution_correct}/{len(results)} ({100*resolution_correct//len(results)}%)")
    
    # Learning
    print("\n" + "=" * 70)
    print("SELF-LEARNING")
    print("=" * 70)
    
    proposed = await learning_engine.analyze_failures(results)
    print(f"Proposed skills: {len(proposed)}")
    
    for skill in proposed:
        print(f"\n- {skill.name}")
        print(f"  Status: {skill.status}")
        print(f"  From failures: {len(skill.source_tickets)} tickets")
        
        # Check format
        has_insights = "Key Insights" in skill.content
        has_rules = "Decision Rules" in skill.content
        has_json_rules = "'route_to':" in skill.content
        
        if has_insights and not has_rules and not has_json_rules:
            print(f"  Format: [GOOD] Uses guidelines, no hardcoding")
        elif has_rules or has_json_rules:
            print(f"  Format: [BAD] Has hardcoded rules")
        else:
            print(f"  Format: [CHECK] Review content")
    
    # Show learned skills
    print("\n" + "=" * 70)
    print("APPROVED LEARNED SKILLS IN SYSTEM")
    print("=" * 70)
    
    learned = ticket_processor._get_approved_learned_skills()
    if learned:
        print(f"Active: {len(learned)} approved skills")
        for name in learned:
            print(f"  - {name}")
    else:
        print("None - ready for first cycle of learning")

if __name__ == "__main__":
    asyncio.run(main())
