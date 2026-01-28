---
name: categorization
description: Categorizes ITSM tickets into standard ITIL types (Incident, Problem, Change Request, Service Request) based on content analysis and business impact.
---

# Ticket Categorization Skill

This skill classifies tickets into ITIL-aligned categories.

## Categories

### Incident
An unplanned interruption to an IT service or reduction in quality.

**Indicators:**
- Something is broken or not working
- Service degradation or outage
- Error messages or failures
- "It was working before"
- Affects current work

**Examples:**
- "My email isn't sending"
- "The application crashes when I click submit"
- "Website is down"
- "Getting error 500"

### Problem
The underlying cause of one or more incidents.

**Indicators:**
- Recurring issues
- Multiple users affected by same issue
- Investigation into root cause requested
- Pattern of similar incidents

**Examples:**
- "Why does the server keep crashing every Monday?"
- "Multiple users reporting slow performance"
- "Need to investigate repeated login failures"

### Change Request
A formal proposal to modify an IT service or system.

**Indicators:**
- Request to add/modify/remove functionality
- System upgrades or updates
- Configuration changes
- New deployments
- Scheduled maintenance

**Examples:**
- "Please upgrade our server to Windows Server 2022"
- "Add a new field to the customer database"
- "Deploy the new version of the CRM"
- "Change the firewall rules for port 443"

### Service Request
A request for information, advice, access, or a standard service.

**Indicators:**
- Access requests (new account, permissions)
- Software installation requests
- Information or "how to" questions
- Standard catalog items
- Onboarding/offboarding tasks

**Examples:**
- "I need access to the finance shared drive"
- "Please install Microsoft Visio on my laptop"
- "How do I reset my password?"
- "New employee starting Monday, needs laptop setup"

## Decision Logic

```
1. Is something broken or degraded?
   → YES: INCIDENT
   → NO: Continue

2. Is this investigating root cause of recurring issues?
   → YES: PROBLEM
   → NO: Continue

3. Is this requesting a modification to a system/service?
   → YES: CHANGE REQUEST
   → NO: Continue

4. Default: SERVICE REQUEST
```

## Output Format

```json
{
    "category": "Incident|Problem|Change Request|Service Request",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of classification decision",
    "alternative_category": "Second most likely category if confidence < 0.8"
}
```
