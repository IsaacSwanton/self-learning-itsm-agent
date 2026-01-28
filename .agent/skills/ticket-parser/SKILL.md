---
name: ticket-parser
description: Parses raw ticket text to extract structured data including title, description, urgency indicators, affected systems, and user contact information.
---

# Ticket Parser Skill

This skill extracts structured information from raw ITSM ticket submissions.

## When to Use

Use this skill when processing a new ticket to extract structured fields from unstructured text.

## Extraction Fields

Extract the following information from ticket text:

### Required Fields
- **Title/Subject**: The main topic or issue summary
- **Description**: Detailed explanation of the problem or request
- **Reporter**: Who submitted the ticket (if identifiable)

### Urgency Indicators
Look for these keywords that indicate urgency:
- **Critical**: "production down", "outage", "emergency", "urgent", "ASAP", "critical"
- **High**: "blocking work", "cannot work", "major issue", "affecting multiple users"
- **Medium**: "affecting work", "workaround available", "intermittent"
- **Low**: "when time permits", "minor", "nice to have", "cosmetic"

### Affected Systems
Identify mentioned systems, applications, or services:
- Email systems (Outlook, Exchange, Gmail)
- Network (VPN, WiFi, connectivity)
- Hardware (laptop, printer, monitor)
- Applications (specific software names)
- Cloud services (Azure, AWS, Office 365)

## Output Format

Return a structured JSON object:
```json
{
    "title": "Extracted title",
    "description": "Full description text",
    "reporter": "User name or email",
    "urgency_level": "Critical|High|Medium|Low",
    "urgency_indicators": ["list", "of", "trigger", "words"],
    "affected_systems": ["system1", "system2"],
    "keywords": ["relevant", "technical", "terms"]
}
```

## Examples

### Example 1: Network Issue
**Input**: "Hi, I can't connect to VPN since this morning. Getting error 'Connection timed out'. Need this fixed urgently as I have client meetings."

**Output**:
```json
{
    "title": "VPN Connection Failure",
    "description": "User cannot connect to VPN since morning. Receiving 'Connection timed out' error. Has client meetings scheduled.",
    "urgency_level": "High",
    "urgency_indicators": ["urgently"],
    "affected_systems": ["VPN"],
    "keywords": ["VPN", "connection", "timeout"]
}
```

### Example 2: Software Request
**Input**: "Could we get Slack installed on the team laptops? We're starting a new project and the client uses it for communication."

**Output**:
```json
{
    "title": "Software Installation Request - Slack",
    "description": "Request to install Slack on team laptops for client project communication.",
    "urgency_level": "Medium",
    "urgency_indicators": [],
    "affected_systems": ["Desktop Applications"],
    "keywords": ["Slack", "installation", "software"]
}
```
