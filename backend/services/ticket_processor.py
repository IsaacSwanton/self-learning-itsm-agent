"""
Ticket Processor Service

Orchestrates ticket processing through the skills pipeline:
1. Parse raw ticket data
2. Apply categorization skill
3. Apply routing skill
4. Apply resolution skill
5. Compare predictions to actual outcomes
"""

import json
from typing import List, Optional, Dict, Any
from ..models import Ticket, TicketPrediction, ProcessingResult
from .skill_loader import skill_loader
from .ollama_client import ollama_client


class TicketProcessor:
    """Processes tickets through the ITSM agent pipeline"""
    
    def __init__(self):
        self.skill_loader = skill_loader
    
    async def process_ticket(self, ticket: Ticket) -> ProcessingResult:
        """Process a single ticket through all skills"""
        
        # Get skill instructions
        categorization_skill = self.skill_loader.get_skill_content("categorization")
        routing_skill = self.skill_loader.get_skill_content("routing")
        resolution_skill = self.skill_loader.get_skill_content("resolution")
        
        # Build the combined prompt with skill context
        system_prompt = self._build_system_prompt(
            categorization_skill,
            routing_skill,
            resolution_skill
        )
        
        prompt = self._build_ticket_prompt(ticket)
        
        # Get prediction from LLM
        prediction_data = await ollama_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # Helper to safely extract string values (LLM may return objects)
        def safe_string(value, default="Unknown"):
            if value is None:
                return default
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                # Try common keys for nested objects
                for key in ['value', 'text', 'name', 'suggested_resolution', 'primary_team', 'category']:
                    if key in value:
                        return str(value[key])
                return str(value)
            return str(value)
        
        def safe_float(value, default=0.5):
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, dict):
                for key in ['value', 'score', 'confidence']:
                    if key in value:
                        try:
                            return float(value[key])
                        except:
                            pass
                return default
            try:
                return float(value)
            except:
                return default
        
        prediction = TicketPrediction(
            ticket_id=ticket.id,
            predicted_category=safe_string(prediction_data.get("category"), "Unknown"),
            predicted_routing=safe_string(prediction_data.get("routing", prediction_data.get("primary_team")), "General Support"),
            predicted_resolution=safe_string(prediction_data.get("resolution", prediction_data.get("suggested_resolution")), "Further investigation required"),
            confidence_scores={
                "category": safe_float(prediction_data.get("category_confidence", prediction_data.get("confidence"))),
                "routing": safe_float(prediction_data.get("routing_confidence")),
                "resolution": safe_float(prediction_data.get("resolution_confidence"))
            }
        )
        
        # Compare with actual values if available
        result = ProcessingResult(
            ticket=ticket,
            prediction=prediction
        )
        
        if ticket.actual_category:
            result.category_correct = self._compare_values(
                prediction.predicted_category,
                ticket.actual_category
            )
        
        if ticket.actual_routing:
            result.routing_correct = self._compare_values(
                prediction.predicted_routing,
                ticket.actual_routing
            )
        
        if ticket.actual_resolution:
            result.resolution_correct = self._compare_resolution(
                prediction.predicted_resolution,
                ticket.actual_resolution
            )
        
        return result
    
    async def process_batch(self, tickets: List[Ticket]) -> List[ProcessingResult]:
        """Process a batch of tickets"""
        results = []
        for ticket in tickets:
            result = await self.process_ticket(ticket)
            results.append(result)
        return results
    
    def _build_system_prompt(
        self,
        categorization_skill: Optional[str],
        routing_skill: Optional[str],
        resolution_skill: Optional[str]
    ) -> str:
        """Build the system prompt with skill instructions"""
        
        base_prompt = """You are an ITSM (IT Service Management) agent specializing in ticket processing.
Your role is to analyze support tickets and provide:
1. Category classification
2. Routing recommendation
3. Resolution suggestion

Respond ONLY with a JSON object in this exact format:
{
    "category": "Incident|Problem|Change Request|Service Request",
    "category_confidence": 0.0-1.0,
    "routing": "Team or group name",
    "routing_confidence": 0.0-1.0,
    "resolution": "Suggested resolution or next steps",
    "resolution_confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your decisions"
}
"""
        
        if categorization_skill:
            base_prompt += f"\n\n## Categorization Guidelines\n{categorization_skill}"
        
        if routing_skill:
            base_prompt += f"\n\n## Routing Guidelines\n{routing_skill}"
        
        if resolution_skill:
            base_prompt += f"\n\n## Resolution Guidelines\n{resolution_skill}"
        
        return base_prompt
    
    def _build_ticket_prompt(self, ticket: Ticket) -> str:
        """Build the prompt for a specific ticket"""
        return f"""Analyze the following ITSM ticket and provide category, routing, and resolution:

**Ticket ID**: {ticket.id}
**Title**: {ticket.title}
**Description**: {ticket.description}
**Created**: {ticket.created_at or 'Not specified'}

Provide your analysis as JSON."""
    
    def _compare_values(self, predicted: str, actual: str) -> bool:
        """Compare predicted and actual values (fuzzy match)"""
        pred_lower = predicted.lower().strip()
        actual_lower = actual.lower().strip()
        
        # Exact match
        if pred_lower == actual_lower:
            return True
        
        # Partial match (one contains the other)
        if pred_lower in actual_lower or actual_lower in pred_lower:
            return True
        
        return False
    
    def _compare_resolution(self, predicted: str, actual: str) -> bool:
        """Compare resolution using semantic similarity and keyword overlap"""
        if not predicted or not actual:
            return False
        
        pred_lower = predicted.lower().strip()
        actual_lower = actual.lower().strip()
        
        # Exact match
        if pred_lower == actual_lower:
            return True
        
        # Partial containment
        if pred_lower in actual_lower or actual_lower in pred_lower:
            return True
        
        # Extract meaningful words (remove common stop words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'them', 'their', 'please', 'try', 'check'
        }
        
        # Action words that indicate similar resolutions
        action_synonyms = {
            'reset': {'reset', 'restart', 'reboot', 'restore', 'reinitialize'},
            'update': {'update', 'upgrade', 'patch', 'install'},
            'install': {'install', 'deploy', 'set up', 'configure'},
            'verify': {'verify', 'check', 'confirm', 'validate', 'test'},
            'restart': {'restart', 'reboot', 'reset', 'power cycle'},
            'configure': {'configure', 'setup', 'set up', 'adjust', 'modify'},
            'recreate': {'recreate', 'rebuild', 'reset', 'create new'},
            'reconnect': {'reconnect', 'connect', 'reestablish', 'restore connection'},
        }
        
        def get_keywords(text):
            words = set()
            for word in text.split():
                # Clean punctuation
                word = ''.join(c for c in word if c.isalnum())
                if word and word not in stop_words and len(word) > 2:
                    words.add(word)
            return words
        
        pred_keywords = get_keywords(pred_lower)
        actual_keywords = get_keywords(actual_lower)
        
        # Calculate keyword overlap (Jaccard similarity)
        if not pred_keywords or not actual_keywords:
            return False
        
        intersection = pred_keywords & actual_keywords
        union = pred_keywords | actual_keywords
        
        jaccard = len(intersection) / len(union) if union else 0
        
        # Check for action word matches (synonyms)
        action_match = False
        for action_group in action_synonyms.values():
            pred_has = any(a in pred_lower for a in action_group)
            actual_has = any(a in actual_lower for a in action_group)
            if pred_has and actual_has:
                action_match = True
                break
        
        # Consider it a match if:
        # - High keyword overlap (>= 40%)
        # - OR at least 2 keywords match AND an action word matches
        if jaccard >= 0.4:
            return True
        if len(intersection) >= 2 and action_match:
            return True
        
        return False


# Singleton instance
ticket_processor = TicketProcessor()

