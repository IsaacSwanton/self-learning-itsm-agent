"""
Tickets Router

API endpoints for ticket upload and processing.
"""

import json
import csv
import io
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from ..models import Ticket, ProcessingResult, ProcessingRun
from ..services.ticket_processor import ticket_processor
from ..services.learning_engine import learning_engine
from ..config import TICKETS_DIR, REPORTS_DIR

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

# In-memory storage for processing runs (in production, use a database)
processing_runs: dict[str, ProcessingRun] = {}


class TicketUploadResponse(BaseModel):
    message: str
    ticket_count: int
    run_id: str


class ProcessingStatusResponse(BaseModel):
    run_id: str
    status: str
    total_tickets: int
    processed_tickets: int
    accuracy: dict


@router.post("/upload", response_model=TicketUploadResponse)
async def upload_tickets(file: UploadFile = File(...)):
    """Upload a ticket dataset (CSV or JSON)"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    content = await file.read()
    content_str = content.decode('utf-8')
    
    tickets = []
    
    if file.filename.endswith('.json'):
        try:
            data = json.loads(content_str)
            # Handle both array and object with "tickets" key
            ticket_data = data if isinstance(data, list) else data.get('tickets', [])
            for t in ticket_data:
                tickets.append(Ticket(**t))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    
    elif file.filename.endswith('.csv'):
        try:
            reader = csv.DictReader(io.StringIO(content_str))
            for row in reader:
                tickets.append(Ticket(
                    id=row.get('id', f"TKT-{len(tickets)+1:04d}"),
                    title=row.get('title', row.get('subject', '')),
                    description=row.get('description', row.get('body', '')),
                    actual_category=row.get('actual_category', row.get('category')),
                    actual_routing=row.get('actual_routing', row.get('routing', row.get('assigned_team'))),
                    actual_resolution=row.get('actual_resolution', row.get('resolution'))
                ))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")
    else:
        raise HTTPException(status_code=400, detail="File must be .json or .csv")
    
    if not tickets:
        raise HTTPException(status_code=400, detail="No tickets found in file")
    
    # Create a processing run
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    run = ProcessingRun(
        id=run_id,
        total_tickets=len(tickets)
    )
    processing_runs[run_id] = run
    
    # Save tickets for processing
    tickets_file = TICKETS_DIR / f"{run_id}.json"
    tickets_file.write_text(
        json.dumps([t.model_dump(mode='json') for t in tickets], indent=2, default=str),
        encoding='utf-8'
    )
    
    return TicketUploadResponse(
        message=f"Uploaded {len(tickets)} tickets successfully",
        ticket_count=len(tickets),
        run_id=run_id
    )


@router.post("/process/{run_id}")
async def process_tickets(run_id: str):
    """Process uploaded tickets through the ITSM agent"""
    
    if run_id not in processing_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = processing_runs[run_id]
    
    # Load tickets
    tickets_file = TICKETS_DIR / f"{run_id}.json"
    if not tickets_file.exists():
        raise HTTPException(status_code=404, detail="Tickets file not found")
    
    ticket_data = json.loads(tickets_file.read_text(encoding='utf-8'))
    tickets = [Ticket(**t) for t in ticket_data]
    
    # Process tickets
    results = []
    for ticket in tickets:
        result = await ticket_processor.process_ticket(ticket)
        results.append(result)
        run.processed_tickets += 1
        
        # Track accuracy
        if result.category_correct:
            run.correct_predictions += 1
    
    run.results = results
    run.completed_at = datetime.utcnow()
    
    # Analyze failures and propose new skills
    proposed = await learning_engine.analyze_failures(results)
    run.proposed_skills = [s.id for s in proposed]
    
    # Save report
    report_file = REPORTS_DIR / f"{run_id}_report.json"
    report_file.write_text(
        json.dumps(run.model_dump(mode='json'), indent=2, default=str),
        encoding='utf-8'
    )
    
    return {
        "run_id": run_id,
        "status": "completed",
        "total_tickets": run.total_tickets,
        "processed_tickets": run.processed_tickets,
        "proposed_skills": len(proposed),
        "results": [r.model_dump(mode='json') for r in results]
    }


@router.get("/status/{run_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(run_id: str):
    """Get the status of a processing run"""
    
    if run_id not in processing_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = processing_runs[run_id]
    
    # Calculate accuracy
    accuracy = {
        "category": 0,
        "routing": 0,
        "resolution": 0
    }
    
    if run.results:
        cat_correct = sum(1 for r in run.results if r.category_correct is True)
        route_correct = sum(1 for r in run.results if r.routing_correct is True)
        res_correct = sum(1 for r in run.results if r.resolution_correct is True)
        
        total = len(run.results)
        accuracy = {
            "category": round(cat_correct / total * 100, 1) if total else 0,
            "routing": round(route_correct / total * 100, 1) if total else 0,
            "resolution": round(res_correct / total * 100, 1) if total else 0
        }
    
    return ProcessingStatusResponse(
        run_id=run_id,
        status="completed" if run.completed_at else "processing",
        total_tickets=run.total_tickets,
        processed_tickets=run.processed_tickets,
        accuracy=accuracy
    )


@router.get("/results/{run_id}")
async def get_results(run_id: str):
    """Get the full results of a processing run"""
    
    if run_id not in processing_runs:
        raise HTTPException(status_code=404, detail="Run not found")
    
    run = processing_runs[run_id]
    
    return {
        "run_id": run_id,
        "completed_at": run.completed_at,
        "total_tickets": run.total_tickets,
        "results": [r.model_dump(mode='json') for r in run.results],
        "proposed_skills": run.proposed_skills
    }
