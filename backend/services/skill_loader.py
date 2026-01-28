"""
Skill Loader Service

Implements the Claude Skills progressive disclosure pattern:
1. Scan .claude/skills/ directory for SKILL.md files
2. Parse YAML frontmatter to get skill metadata
3. Load full instructions when skill is activated
4. Provide skill context to LLM calls
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional
from ..config import SKILLS_DIR, PROPOSED_SKILLS_DIR
from ..models import SkillMetadata


class SkillLoader:
    """Manages loading and discovery of Claude Skills"""
    
    def __init__(self):
        self._skill_cache: Dict[str, SkillMetadata] = {}
        self._content_cache: Dict[str, str] = {}
        
    def discover_skills(self) -> List[SkillMetadata]:
        """Scan skills directory and load metadata from all SKILL.md files"""
        skills = []
        
        # Load approved skills from .claude/skills/
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    metadata = self._parse_skill_metadata(skill_file, is_approved=True)
                    if metadata:
                        skills.append(metadata)
                        self._skill_cache[metadata.name] = metadata
        
        # Load approved skills from proposed_skills that were approved
        for skill_file in PROPOSED_SKILLS_DIR.glob("*.md"):
            if skill_file.stem.startswith("approved_"):
                metadata = self._parse_skill_metadata(skill_file, is_approved=True)
                if metadata:
                    skills.append(metadata)
                    self._skill_cache[metadata.name] = metadata
        
        return skills
    
    def _parse_skill_metadata(self, skill_file: Path, is_approved: bool = True) -> Optional[SkillMetadata]:
        """Parse YAML frontmatter from a SKILL.md file"""
        try:
            content = skill_file.read_text(encoding='utf-8')
            
            # Extract YAML frontmatter between --- delimiters
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not frontmatter_match:
                return None
            
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            
            return SkillMetadata(
                name=frontmatter.get('name', skill_file.parent.name),
                description=frontmatter.get('description', ''),
                file_path=str(skill_file),
                is_approved=is_approved
            )
        except Exception as e:
            print(f"Error parsing skill {skill_file}: {e}")
            return None
    
    def get_skill_content(self, skill_name: str) -> Optional[str]:
        """Load the full content of a skill (progressive disclosure step 2)"""
        if skill_name in self._content_cache:
            return self._content_cache[skill_name]
        
        if skill_name not in self._skill_cache:
            return None
        
        skill_path = Path(self._skill_cache[skill_name].file_path)
        try:
            content = skill_path.read_text(encoding='utf-8')
            # Strip the frontmatter, return just the instructions
            content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
            self._content_cache[skill_name] = content
            return content
        except Exception as e:
            print(f"Error loading skill content {skill_name}: {e}")
            return None
    
    def get_skill_summary(self) -> str:
        """Get a summary of all available skills for the LLM context"""
        skills = self.discover_skills()
        if not skills:
            return "No skills available."
        
        summary_lines = ["Available ITSM Skills:"]
        for skill in skills:
            summary_lines.append(f"- **{skill.name}**: {skill.description}")
        
        return "\n".join(summary_lines)
    
    def get_skills_for_task(self, task_type: str) -> List[SkillMetadata]:
        """Get relevant skills for a specific task type"""
        skills = self.discover_skills()
        task_keywords = {
            "categorization": ["categoriz", "classif", "type"],
            "routing": ["rout", "assign", "team", "group"],
            "resolution": ["resolv", "solution", "fix", "answer"]
        }
        
        keywords = task_keywords.get(task_type.lower(), [])
        relevant = []
        
        for skill in skills:
            desc_lower = skill.description.lower()
            if any(kw in desc_lower for kw in keywords):
                relevant.append(skill)
        
        return relevant


# Singleton instance
skill_loader = SkillLoader()
