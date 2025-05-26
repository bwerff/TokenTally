# SOC 2 Risk Assessment

This document captures the major risks identified for TokenTally's SOC 2 program and the planned controls to mitigate them. It will be expanded as the compliance initiative progresses.

## Identified Risks and Controls

| Risk | Impact | Planned Control |
| --- | --- | --- |
| **Unauthorized access to production data** | Compromise of customer usage information or invoice details. | Enforce role-based access control, mandatory multi-factor authentication and quarterly access reviews. |
| **Loss of audit logs** | Inability to prove compliance or investigate incidents. | Ship logs to an append-only store with daily backups and retention policies. |
| **Billing data tampering** | Financial inaccuracies leading to customer disputes. | Implement immutable ledger entries with cryptographic hashes and automated integrity checks. |
| **Third-party service outage** (e.g. Stripe, cloud provider) | Delayed invoicing or downtime. | Queue events until upstreams recover and periodically test disaster‑recovery procedures. |
| **Insufficient vulnerability management** | Unpatched systems could be exploited. | Weekly dependency scans and monthly OS patching, tracked in the security backlog. |
| **Employee offboarding gaps** | Former staff retain system access. | Automate account deactivation on HR termination events and run monthly audits. |
| **Data residency misconfiguration** | Data stored outside agreed regions. | Deployment automation validates region settings and alerts on drift. |

## Review Schedule

The risk register will be reviewed at least twice per year and whenever significant infrastructure or process changes occur.
