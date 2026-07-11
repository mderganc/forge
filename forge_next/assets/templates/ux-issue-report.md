# UX Issue Report Template

Use for each defect found in `forge test --mode ux`. Persist objects in `state.custom.ux_issues` / `.test-ux-issues.json`.

```markdown
## UX-N — <short title>

- **Severity:** critical | high | medium | low
- **Page / feature:** …
- **Scenario:** S…
- **Environment:** base URL, browser, role, account

### Steps to reproduce
1. …
2. …
3. …

### Expected
…

### Actual
…

### Evidence
- Screenshot: …
- Console: …
- Network: …
```

JSON shape:

```json
{
  "id": "UX-1",
  "title": "Share dialog closes without saving invite",
  "severity": "high",
  "page": "/reports/42",
  "feature": "Share",
  "scenario_id": "S3",
  "steps": [
    "Open report 42 as member",
    "Click Share",
    "Enter teammate email",
    "Click Invite"
  ],
  "expected": "Invitee listed under Shared with; success toast",
  "actual": "Dialog closes; Shared with remains empty",
  "screenshots": ["artifacts/ux-1-share.png"],
  "console_errors": ["TypeError: ..."],
  "network_errors": ["POST /api/shares 500"]
}
```
