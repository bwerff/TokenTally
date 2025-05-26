# SOC 2 Type II Monitoring & Evidence Plan

This document outlines how TokenTally maintains continuous compliance once the Type I audit is complete. The activities below ensure controls remain effective and that we gather evidence for the Type II report.

## Ongoing monitoring

- **Log aggregation** – application and infrastructure logs are forwarded to our SIEM within 30 seconds. Alerts trigger PagerDuty for high-risk events.
- **Vulnerability scanning** – containers and dependencies are scanned nightly. Critical findings are patched within 48 hours.
- **Access reviews** – engineers and contractors are reviewed quarterly. Off-boarding removes credentials within 24 hours.
- **Infrastructure as code** – Terraform and Helm changes require PR approval and are automatically tested in CI.
- **Backup validation** – database backups are restored to a staging environment every month to verify integrity.

## Evidence collection

| Evidence source              | Collection frequency | Responsible role |
| -----------------------------| -------------------- | ---------------- |
| SIEM alert exports           | Weekly              | Security Lead    |
| Patch management reports     | Monthly             | DevOps           |
| Access review checklist      | Quarterly           | CTO              |
| Backup restore logs          | Monthly             | DevOps           |
| Training completion records  | On new hire / annual| People Ops       |

All evidence is stored in an encrypted S3 bucket with write-once permissions. Auditors receive read-only access during the Type II assessment period.
