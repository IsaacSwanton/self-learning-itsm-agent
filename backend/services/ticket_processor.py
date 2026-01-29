"""
Ticket Processor Service

Orchestrates ticket processing through the skills pipeline:
1. Parse raw ticket data
2. Apply categorization skill
3. Apply routing skill
4. Apply resolution skill
5. Compare predictions to actual outcomes

Note on Learned Skills:
- Approved learned skills are included as SUPPLEMENTARY GUIDANCE only
- They provide contextual insights from past failures, not hard rules
- The LLM's general reasoning is primary; learned insights are secondary
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
    
    def _get_approved_learned_skills(self) -> Dict[str, str]:
        """Get all approved learned skills from proposed_skills directory.
        
        Returns a dict of skill_name -> skill_content for all approved skills.
        These are used as supplementary guidance in the system prompt.
        """
        learned_skills = {}
        try:
            # Get all skills that are approved (in data/proposed_skills/approved_*.md)
            all_skills = self.skill_loader.discover_skills()
            
            # Filter to only approved learned skills (from proposed_skills directory)
            # by checking if they're not in the core skills
            core_skill_names = {'categorization', 'routing', 'resolution', 'ticket-parser'}
            
            for skill in all_skills:
                if skill.name not in core_skill_names:
                    # This is a learned skill - get its content
                    content = self.skill_loader.get_skill_content(skill.name)
                    if content:
                        learned_skills[skill.name] = content
        except Exception as e:
            print(f"Error loading approved learned skills: {e}")
        
        return learned_skills
    
    async def process_ticket(self, ticket: Ticket) -> ProcessingResult:
        """Process a single ticket through all skills"""
        
        # Get skill instructions for core ITSM skills
        categorization_skill = self.skill_loader.get_skill_content("categorization")
        routing_skill = self.skill_loader.get_skill_content("routing")
        resolution_skill = self.skill_loader.get_skill_content("resolution")
        ticket_parser_skill = self.skill_loader.get_skill_content("ticket-parser")
        
        # Get approved learned skills as supplementary guidance
        learned_skills = self._get_approved_learned_skills()
        
        # Build the combined prompt with core skill context and learned insights
        system_prompt = self._build_system_prompt(
            categorization_skill,
            routing_skill,
            resolution_skill,
            ticket_parser_skill,
            learned_skills
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
        resolution_skill: Optional[str],
        ticket_parser_skill: Optional[str] = None,
        learned_skills: Optional[Dict[str, str]] = None
    ) -> str:
        """Build the system prompt with core ITSM skill instructions and learned insights
        
        Args:
            categorization_skill: Core categorization guidelines
            routing_skill: Core routing guidelines
            resolution_skill: Core resolution guidelines
            ticket_parser_skill: Optional ticket parsing guidelines
            learned_skills: Optional dict of learned skill name -> content
        
        Returns:
            Complete system prompt for the LLM
            
        Note: Core skills are primary. Learned skills provide supplementary contextual
        guidance from past failures - they are secondary to the LLM's reasoning.
        """
        
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
        
        # Add core skills to the prompt (in order of application)
        if ticket_parser_skill:
            base_prompt += f"\n\n## Ticket Parsing Guidelines\n{ticket_parser_skill}"
        
        if categorization_skill:
            base_prompt += f"\n\n## Categorization Guidelines\n{categorization_skill}"
        
        if routing_skill:
            base_prompt += f"\n\n## Routing Guidelines\n{routing_skill}"
        
        if resolution_skill:
            base_prompt += f"\n\n## Resolution Guidelines\n{resolution_skill}"
        
        # Add learned skills as supplementary guidance if available
        if learned_skills:
            base_prompt += "\n\n## Supplementary Insights from Learned Skills\n"
            base_prompt += "The following insights come from analyzing past incorrect predictions. "
            base_prompt += "Use them as contextual guidance to inform your reasoning, but your primary "
            base_prompt += "decision-making should follow the core guidelines above.\n"
            
            for skill_name, skill_content in learned_skills.items():
                base_prompt += f"\n### {skill_name}\n{skill_content}"
        
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

