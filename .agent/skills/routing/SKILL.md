---
name: routing
description: Determines the appropriate support team or assignment group for ITSM tickets based on category, affected systems, and required expertise.
---

# Ticket Routing Skill

This skill assigns tickets to the appropriate support team or assignment group.

## Support Teams

### Level 1 Service Desk
**Responsibilities:**
- First point of contact for all tickets
- Password resets and account unlocks
- Basic troubleshooting
- Standard service requests
- Ticket triage and escalation

**Keywords:** password, login, access, new user, basic, simple

### Desktop Support
**Responsibilities:**
- Hardware issues (laptops, desktops, monitors)
- Software installation and configuration
- Operating system problems
- Printer issues
- Local device troubleshooting

**Keywords:** laptop, computer, printer, install, software, Windows, Mac

### Network Team
**Responsibilities:**
- Network connectivity issues
- VPN problems
- WiFi troubleshooting
- Firewall changes
- DNS and DHCP issues

**Keywords:** VPN, network, WiFi, internet, connectivity, firewall, DNS

### Server Team
**Responsibilities:**
- Server hardware and OS
- Virtual machines
- Storage systems
- Backups and recovery
- Server-side applications

**Keywords:** server, VM, virtual, backup, storage, disk space, performance

### Email Support Team
**Responsibilities:**
- Email client issues
- Email server problems
- Calendar and scheduling
- Distribution lists
- Email security (spam, phishing)

**Keywords:** email, Outlook, Exchange, calendar, mailbox, spam

### Application Support
**Responsibilities:**
- Business application issues
- ERP, CRM systems
- Database problems
- Custom application bugs
- Integration issues

**Keywords:** application, system, database, SAP, Salesforce, error, bug

### Security Team
**Responsibilities:**
- Security incidents
- Malware/virus reports
- Phishing attempts
- Access reviews
- Security policy violations

**Keywords:** virus, malware, security, phishing, suspicious, breach, hack

### Cloud Services Team
**Responsibilities:**
- Cloud platform issues (Azure, AWS, GCP)
- SaaS application problems
- Office 365 issues
- Cloud infrastructure

**Keywords:** Azure, AWS, cloud, Office 365, SharePoint, Teams, OneDrive

## Routing Decision Matrix

| Category | Primary System | Route To |
|----------|---------------|----------|
| Incident | Email | Email Support Team |
| Incident | Network/VPN | Network Team |
| Incident | Hardware | Desktop Support |
| Incident | Server | Server Team |
| Incident | Security | Security Team |
| Incident | Application | Application Support |
| Service Request | Account/Access | Level 1 Service Desk |
| Service Request | Software Install | Desktop Support |
| Change Request | Network | Network Team |
| Change Request | Server | Server Team |
| Change Request | Application | Application Support |
| Problem | Any | Escalate to Engineering |

## Escalation Rules

1. **Critical/Urgent Incidents**: Route directly to on-call team
2. **Security Incidents**: Always copy Security Team
3. **VIP Users**: Flag for priority handling
4. **Multiple Team Involvement**: Assign to primary team, add others as FYI

## Output Format

```json
{
    "primary_team": "Team name",
    "confidence": 0.0-1.0,
    "escalation_required": true|false,
    "additional_teams": ["Team1", "Team2"],
    "priority_flag": "VIP|Critical|Normal",
    "reasoning": "Brief explanation of routing decision"
}
```
