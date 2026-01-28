"""
Learning Engine Service

Implements the learning loop:
1. Analyze cases where agent was incorrect
2. Identify patterns in failures
3. Generate proposed skills as Markdown
4. Queue proposals for human review
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from ..config import PROPOSED_SKILLS_DIR
from ..models import ProcessingResult, ProposedSkill
from .ollama_client import ollama_client


# Skill template for generated skills - matches base skill format
SKILL_TEMPLATE = """---
name: {name}
description: {description}
version: 1.0
generated: {timestamp}
source_tickets: {ticket_ids}
---

# {title}

{summary}

## When to Apply

This skill should be used when processing tickets that match these patterns:
{trigger_patterns}

## Learned Patterns

{patterns_section}

## Decision Rules

{rules_section}

## Examples

{examples_section}

## Output Format

```json
{{
    "{output_field}": "value based on rules above",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation citing which rule or pattern was matched"
}}
```
"""


class LearningEngine:
    """Generates new skill proposals from processing failures"""
    
    def __init__(self):
        self.proposed_skills: Dict[str, ProposedSkill] = {}
        self._load_existing_proposals()
    
    def _load_existing_proposals(self):
        """Load existing proposed skills from disk"""
        for skill_file in PROPOSED_SKILLS_DIR.glob("pending_*.json"):
            try:
                data = json.loads(skill_file.read_text(encoding='utf-8'))
                skill = ProposedSkill(**data)
                self.proposed_skills[skill.id] = skill
            except Exception as e:
                print(f"Error loading proposed skill {skill_file}: {e}")
    
    async def analyze_failures(self, results: List[ProcessingResult]) -> List[ProposedSkill]:
        """Analyze failed predictions and propose new skills"""
        
        # Collect ONLY actual failures for each type
        category_failures = []
        routing_failures = []
        resolution_failures = []
        
        for result in results:
            # Only include if explicitly False (not None or True)
            if result.category_correct is False:
                category_failures.append(result)
            if result.routing_correct is False:
                routing_failures.append(result)
            if result.resolution_correct is False:
                resolution_failures.append(result)
        
        print(f"[Learning Engine] Analyzing {len(results)} results:")
        print(f"  - Category failures: {len(category_failures)} tickets")
        print(f"  - Routing failures: {len(routing_failures)} tickets")
        print(f"  - Resolution failures: {len(resolution_failures)} tickets")
        
        # Debug: show which tickets are failures
        if category_failures:
            print(f"  - Category failure IDs: {[r.ticket.id for r in category_failures]}")
        if routing_failures:
            print(f"  - Routing failure IDs: {[r.ticket.id for r in routing_failures]}")
        if resolution_failures:
            print(f"  - Resolution failure IDs: {[r.ticket.id for r in resolution_failures]}")
        
        proposed = []
        
        # Require at least 2 failures to propose a skill (reduces noise)
        if len(category_failures) >= 2:
            print(f"[Learning Engine] Proposing categorization skill...")
            skill = await self._propose_skill(category_failures, "categorization")
            if skill:
                proposed.append(skill)
                print(f"[Learning Engine] Created skill: {skill.name}")
        
        if len(routing_failures) >= 2:
            print(f"[Learning Engine] Proposing routing skill...")
            skill = await self._propose_skill(routing_failures, "routing")
            if skill:
                proposed.append(skill)
                print(f"[Learning Engine] Created skill: {skill.name}")
        
        if len(resolution_failures) >= 2:
            print(f"[Learning Engine] Proposing resolution skill...")
            skill = await self._propose_skill(resolution_failures, "resolution")
            if skill:
                proposed.append(skill)
                print(f"[Learning Engine] Created skill: {skill.name}")
        
        print(f"[Learning Engine] Total proposed skills: {len(proposed)}")
        return proposed
    
    async def _propose_skill(
        self,
        failures: List[ProcessingResult],
        skill_type: str
    ) -> ProposedSkill | None:
        """Propose a skill to improve predictions"""
        
        # Format examples strictly from failures only
        examples = self._format_failure_examples(failures, skill_type)
        
        prompt = f"""Analyze these ITSM ticket {skill_type} mistakes and identify patterns:

{examples}

Based on these failures, provide:
1. Key patterns that were missed (specific keywords, phrases, or contexts)
2. Clear rules to correctly handle similar cases
3. A brief description of the skill

Respond with JSON:
{{
    "skill_name": "short-descriptive-name",
    "description": "One sentence description",
    "patterns": ["pattern 1", "pattern 2"],
    "rules": ["rule 1", "rule 2", "rule 3"]
}}"""
        
        system_prompt = """You are an expert at analyzing ITSM ticket processing mistakes.
Identify the patterns that led to incorrect predictions and provide clear rules to prevent similar errors.
Respond with ONLY valid JSON, no markdown formatting."""
        
        response = await ollama_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        skill_id = f"{skill_type}-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat()
        ticket_ids = [r.ticket.id for r in failures]
        
        # Create skill from response or fallback
        if "error" in response:
            print(f"[Learning Engine] LLM response parsing failed, using structured fallback")
            skill_content = self._create_structured_skill(failures, skill_type, timestamp, {})
        else:
            skill_content = self._create_structured_skill(failures, skill_type, timestamp, response)
        
        skill_name = response.get('skill_name', f'learned-{skill_type}')
        skill_description = response.get('description', f'Learned {skill_type} patterns from {len(failures)} failed predictions')
        
        # Safely extract patterns (LLM might return dicts or other types)
        raw_patterns = response.get('patterns', [])
        patterns_list = []
        for p in raw_patterns[:3]:
            if isinstance(p, str):
                patterns_list.append(p)
            elif isinstance(p, dict):
                patterns_list.append(str(p.get('pattern', p.get('name', str(p)))))
            else:
                patterns_list.append(str(p))
        
        skill = ProposedSkill(
            id=skill_id,
            name=skill_name,
            description=skill_description,
            trigger_pattern=", ".join(patterns_list) if patterns_list else f"Similar {skill_type} issues",
            content=skill_content,
            source_tickets=ticket_ids
        )
        
        # Save to disk
        self._save_proposal(skill)
        self.proposed_skills[skill.id] = skill
        
        return skill
    
    def _format_failure_examples(
        self,
        failures: List[ProcessingResult],
        skill_type: str
    ) -> str:
        """Format failure examples for the prompt"""
        examples = []
        for i, result in enumerate(failures[:5], 1):  # Limit to 5 examples
            ticket = result.ticket
            prediction = result.prediction
            
            if skill_type == "categorization":
                predicted = prediction.predicted_category
                actual = ticket.actual_category
            elif skill_type == "routing":
                predicted = prediction.predicted_routing
                actual = ticket.actual_routing
            else:
                predicted = prediction.predicted_resolution
                actual = ticket.actual_resolution
            
            examples.append(f"""
**Ticket {ticket.id}**: {ticket.title}
- Description: {ticket.description[:200]}...
- Predicted: {predicted}
- Correct answer: {actual}
""")
        
        return "\n".join(examples)
    
    def _create_structured_skill(
        self,
        failures: List[ProcessingResult],
        skill_type: str,
        timestamp: str,
        llm_response: Dict[str, Any]
    ) -> str:
        """Create a properly formatted skill from failure analysis"""
        
        # Build examples section
        examples_list = []
        for result in failures[:5]:
            ticket = result.ticket
            pred = result.prediction
            if skill_type == "categorization":
                examples_list.append(
                    f"### {ticket.title}\n"
                    f"**Description**: {ticket.description[:150]}...\n"
                    f"**Incorrect**: {pred.predicted_category}\n"
                    f"**Correct**: {ticket.actual_category}\n"
                )
            elif skill_type == "routing":
                examples_list.append(
                    f"### {ticket.title}\n"
                    f"**Description**: {ticket.description[:150]}...\n"
                    f"**Incorrect**: {pred.predicted_routing}\n"
                    f"**Correct**: {ticket.actual_routing}\n"
                )
            else:
                examples_list.append(
                    f"### {ticket.title}\n"
                    f"**Description**: {ticket.description[:150]}...\n"
                    f"**Incorrect suggestion**: {pred.predicted_resolution[:100]}...\n"
                    f"**Correct resolution**: {ticket.actual_resolution}\n"
                )
        
        # Build patterns section
        patterns = llm_response.get('patterns', [])
        if patterns:
            patterns_section = "\n".join([f"- {p}" for p in patterns])
        else:
            # Extract patterns from ticket content
            patterns_section = "Patterns identified from failure analysis:\n"
            for result in failures[:3]:
                patterns_section += f"- Keywords from '{result.ticket.title}'\n"
        
        # Build rules section
        rules = llm_response.get('rules', [])
        if rules:
            rules_section = "\n".join([f"{i}. {r}" for i, r in enumerate(rules, 1)])
        else:
            rules_section = f"""1. When ticket matches patterns above, apply the correct {skill_type}
2. Check for similar keywords and context before making predictions
3. Reference the examples above for guidance on similar cases"""
        
        # Build trigger patterns
        if patterns:
            trigger_patterns = "\n".join([f"- {p}" for p in patterns[:5]])
        else:
            trigger_patterns = f"- Tickets similar to the examples below"
        
        # Map skill type to output field
        output_fields = {
            "categorization": "category",
            "routing": "primary_team",
            "resolution": "suggested_resolution"
        }
        
        return SKILL_TEMPLATE.format(
            name=llm_response.get('skill_name', f'learned-{skill_type}-v1'),
            description=llm_response.get('description', f'Learned {skill_type} improvement skill'),
            timestamp=timestamp,
            ticket_ids=", ".join([r.ticket.id for r in failures]),
            title=f"Learned {skill_type.title()} Patterns",
            summary=f"This skill was generated from analyzing {len(failures)} incorrect {skill_type} predictions. "
                   f"It captures patterns that should be recognized to improve future accuracy.",
            trigger_patterns=trigger_patterns,
            patterns_section=patterns_section,
            rules_section=rules_section,
            examples_section="\n".join(examples_list),
            output_field=output_fields.get(skill_type, skill_type)
        )
    
    def _save_proposal(self, skill: ProposedSkill):
        """Save a proposed skill to disk"""
        file_path = PROPOSED_SKILLS_DIR / f"pending_{skill.id}.json"
        file_path.write_text(
            json.dumps(skill.model_dump(), indent=2, default=str),
            encoding='utf-8'
        )
    
    def get_pending_skills(self) -> List[ProposedSkill]:
        """Get all pending skill proposals"""
        return [s for s in self.proposed_skills.values() if s.status == "pending"]
    
    def approve_skill(self, skill_id: str) -> bool:
        """Approve a proposed skill"""
        if skill_id not in self.proposed_skills:
            return False
        
        skill = self.proposed_skills[skill_id]
        skill.status = "approved"
        
        # Save the skill as an approved SKILL.md
        approved_path = PROPOSED_SKILLS_DIR / f"approved_{skill.name}.md"
        approved_path.write_text(skill.content, encoding='utf-8')
        
        # Remove the pending JSON
        pending_path = PROPOSED_SKILLS_DIR / f"pending_{skill_id}.json"
        if pending_path.exists():
            pending_path.unlink()
        
        return True
    
    def reject_skill(self, skill_id: str) -> bool:
        """Reject a proposed skill"""
        if skill_id not in self.proposed_skills:
            return False
        
        skill = self.proposed_skills[skill_id]
        skill.status = "rejected"
        
        # Remove from disk
        pending_path = PROPOSED_SKILLS_DIR / f"pending_{skill_id}.json"
        if pending_path.exists():
            pending_path.unlink()
        
        del self.proposed_skills[skill_id]
        return True


# Singleton instance
learning_engine = LearningEngine()
