# HIPAA-minded controls (demo)

This demo is **synthetic only**. Controls shown for analyst discussion:

| Control | Demo behavior |
|---|---|
| Least privilege / operator gate | No SOAP write until human Code Review signoff |
| Vault retention | Original packet reference kept separate from derived work items |
| Shared day sheet handling | Resource Time / Daily Billing stays on the batch; not treated as a charge patient |
| Pre-write validation | Required fields checked before CreatePatient / CreateEncounter |
| Fail-safe status | Approved never mirrored while remote is still Draft |
| Audit trail | Interface call log + event / incident history |
| Schedule gaps | Gap flags block approve; Office notes keep the issue visible |

Not a compliance certification. Not production PHI.
