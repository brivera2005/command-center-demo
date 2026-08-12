# Architecture

## Purpose

ClearBilling Command Center Demo is a **workflow sandbox** of the production Command Center loop used for multi-facility anesthesia and clinical charge processing, without any real PHI and without shipping proprietary production UI.

## What is intentionally different

Production Command Center has a richer operator chrome, PDF OCR / packet splicing, vault image caching, and live vendor integrations. Those stay private. This demo keeps the same analyst-visible controls: vaulted originals, coding gates, human signoff, SOAP-shaped CreatePatient/CreateEncounter, fail-safe Draft/Approved sync, Archive / Office / Audit.

## Data flow

1. Intake receives a practice-tagged packet (JSON stand-in for a multi-patient PDF).
2. Vault reference preserves the original packet; shared Resource Time / Daily Billing sheets stay attached to the batch.
3. Parse emits one work item per patient with structured coding fields.
4. Code Review UI requires human medical coding review and operator signoff. Open schedule gaps block approve.
5. Middleware runs SOAP-shaped CreatePatient then CreateEncounter (WSDL-style names) and stores Draft status.
6. Sync reads remote status. Approved is mirrored only after the mock PM/EHR confirms Approved.
7. Archive retains patient outcomes; Office holds schedule-gap / hold notes; Audit shows interface + event history.

## Components

| Piece | Role |
|---|---|
| `app.py` | Flask UI + API, approval/hold/office gates, event/incident log |
| `middleware/mock_pm_api.py` | SOAP/REST-shaped interface, validation, fail-safe sync |
| `templates/index.html` | Teaching UI for Vault / Code Review / Archive / Office / Audit |
| `data/sample_packets.json` | Synthetic packets only |
| `tests/test_pipeline.py` | Payload + fail-safe regression scripts |

## Analyst mapping

- Needs analysis -> structured work-item schema and review screens
- Interface testing -> CreatePatient/CreateEncounter validation + field mapping
- Testing methodology -> pytest scripts with signoff gate
- Production support -> incident objects for validation failures; Office gap notes
- HIPAA controls -> vault ref, human gate, fail-safe sync, synthetic-only demo data
- IP hygiene -> public sandbox proves the loop without cloning live product chrome
