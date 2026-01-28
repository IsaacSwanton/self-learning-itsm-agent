---
name: resolution
description: Suggests resolution steps or solutions for ITSM tickets based on common patterns, known errors, and best practices.
---

# Resolution Suggestion Skill

This skill provides resolution recommendations based on ticket content.

## Resolution Patterns

### Password & Access Issues

**Pattern**: Password reset, locked account, forgotten credentials
**Resolution Steps**:
1. Verify user identity (security questions or manager approval)
2. Reset password via Active Directory / Identity Management
3. Provide temporary password with forced change on next login
4. Confirm user can log in successfully
5. Document in ticket and close

---

### VPN Connection Issues

**Pattern**: VPN not connecting, timeout errors, authentication failures
**Resolution Steps**:
1. Verify user has valid VPN license/access
2. Check if VPN client is up to date
3. Test network connectivity (can reach internet?)
4. Try alternate VPN server/gateway
5. Check if issue is widespread (check monitoring)
6. If persistent, collect VPN logs and escalate to Network Team

**Quick Fix**: Clear VPN client cache and reconnect

---

### Email Not Working

**Pattern**: Outlook not syncing, cannot send/receive, connection to Exchange failed
**Resolution Steps**:
1. Check Outlook is in Online mode (not Work Offline)
2. Verify network connectivity
3. Check Exchange server status (monitoring dashboard)
4. Repair Outlook profile or recreate
5. Clear Outlook cache if sync issues persist
6. Escalate to Email Support if server-side issue

---

### Software Installation

**Pattern**: Request to install software
**Resolution Steps**:
1. Verify software is on approved list
2. Check license availability
3. If approved: Deploy via SCCM/Intune or manual install
4. If not approved: Submit software request form for approval
5. Verify installation successful
6. Document and close

---

### Slow Computer Performance

**Pattern**: Computer running slow, applications hanging
**Resolution Steps**:
1. Check available disk space (need >10% free)
2. Check RAM usage (Task Manager)
3. Scan for malware/viruses
4. Clear temporary files and browser cache
5. Check for Windows updates pending
6. If hardware older than 5 years, consider replacement

---

### Printer Issues

**Pattern**: Cannot print, printer offline, print jobs stuck
**Resolution Steps**:
1. Restart print spooler service
2. Clear print queue
3. Check printer is online and has paper/toner
4. Remove and re-add printer
5. Update printer drivers
6. If network printer, verify network connectivity

---

### Application Errors/Crashes

**Pattern**: Application not starting, crashes, error messages
**Resolution Steps**:
1. Note exact error message
2. Restart the application
3. Clear application cache/temp files
4. Reinstall/repair application
5. Check for updates or patches
6. Collect logs and escalate to Application Support

---

## Resolution Templates

### Standard Acknowledgment
> "Thank you for contacting IT Support. We have received your request and are working on it. Expected resolution time: [SLA]."

### Request More Information
> "To assist you further, please provide: [specific information needed]. This will help us resolve your issue faster."

### Resolution Confirmation
> "Your issue has been resolved. [Brief description of what was done]. Please confirm if everything is working correctly. If the issue persists, please reply to this ticket."

## Output Format

```json
{
    "suggested_resolution": "Primary resolution recommendation",
    "resolution_steps": ["Step 1", "Step 2", "Step 3"],
    "estimated_time": "Quick fix|30 min|1-2 hours|Requires escalation",
    "knowledge_base_match": "KB article ID if applicable",
    "requires_escalation": true|false,
    "confidence": 0.0-1.0
}
```

## Confidence Guidelines

- **0.9-1.0**: Exact match with known resolution pattern
- **0.7-0.9**: Similar issue with likely resolution
- **0.5-0.7**: Partial match, may need additional troubleshooting
- **<0.5**: Novel issue, recommend escalation

When confidence is below 0.7, always include: "If this resolution does not work, the ticket will be escalated to a specialist team."
