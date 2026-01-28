---
name: Email Routing Skill
description: Analyzing keywords in email descriptions to route tickets correctly
version: 1.0
generated: 2026-01-28T14:34:09.665832
source_tickets: TKT-001, TKT-002, TKT-006
---

# Learned Routing Patterns

This skill was generated from analyzing 3 incorrect routing predictions. It captures patterns that should be recognized to improve future accuracy.

## When to Apply

This skill should be used when processing tickets that match these patterns:
- outlook|email|disconnected
- project management|software installation
- laptop setup|new employee

## Learned Patterns

- outlook|email|disconnected
- project management|software installation
- laptop setup|new employee

## Decision Rules

1. {'pattern': 'outlook|email|disconnected', 'route_to': 'Email Support Team'}
2. {'pattern': 'project management|software installation', 'route_to': 'Desktop Support'}
3. {'pattern': ['laptop', 'setup', 'new employee'], 'route_to': 'Desktop Support'}

## Examples

### Cannot access email - Outlook connection error
**Description**: Hi, I've been unable to send or receive emails since 8am this morning. Outlook keeps showing 'Disconnected' in the bottom right corner. I've tried res...
**Incorrect**: General Support
**Correct**: Email Support Team

### Request for project management software
**Description**: Our team is starting a new project next month and we'd like to request installation of Asana for project tracking. We have 5 team members who would ne...
**Incorrect**: Application Support Team
**Correct**: Desktop Support

### New employee laptop setup
**Description**: New employee Sarah Johnson is starting on Monday February 3rd in the Marketing department. She will need a laptop with standard software plus Adobe Cr...
**Incorrect**: Level 1 Service Desk
**Correct**: Desktop Support


## Output Format

```json
{
    "primary_team": "value based on rules above",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation citing which rule or pattern was matched"
}
```
