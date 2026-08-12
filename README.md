# ClearBilling Command Center Demo

**Workflow sandbox** of ClearBilling **Command Center**, the live clinical charge-operations application I design, maintain, test, train on, and support.

> **Synthetic data only.** No real patient PHI, credentials, or production secrets.  
> **Not the production UI.** Live chrome, PDF OCR, vault image cache, vendor integrations, and operator tooling are withheld for proprietary protection. This repo proves the **same operational loop** interviewers can run locally.

**Author:** Benjamin M. Rivera  
**Links:** [LinkedIn](https://linkedin.com/in/brivera2005) · [GitHub](https://github.com/brivera2005) · [Healthcare index](https://github.com/brivera2005/healthcare-portfolio)

---

## What matches live vs what stays private

| Same as production | Intentionally withheld |
|:--|:--|
| Vault → Code Review → Interface → Archive / Office / Audit loop | Production visual design and operator chrome |
| Medical coding gates (CPT/ASA, laterality, DOB, schedule gaps) | Real PDF OCR / packet splicing pipeline |
| Human signoff before PM/EHR write | Live PM/EHR credentials and vendor payloads |
| Fail-safe Draft → Approved sync only after interface confirms | Production vault image cache and practice configs |
| Shared Resource Time / Daily Billing day-sheet rules | Internal training content beyond this public guide |

Screenshots in this repo are of **this sandbox**, not production. That is deliberate.

---

## What you are looking at

Live Command Center processes multi-patient anesthesia and clinical charge packets across many practices and facilities. This repo is a runnable teaching model of that same loop:

1. **Intake** - Practice-tagged multi-patient packet (PDF stand-in as JSON)
2. **Vault** - Immutable original retained; shared Resource Time / Daily Billing day sheet stays on the batch
3. **Parse** - Split into structured patient work items
4. **Code Review** - Human medical coding review (CPT/ASA, laterality, identity/DOB, schedule gaps) with editable fields and operator signoff
5. **Interface** - Mock PM/EHR SOAP `CreatePatient` + `CreateEncounter`, then REST status update
6. **Fail-safe sync** - Draft vs Approved mirrors only when the interface confirms Approved
7. **Archive / Office / Audit** - Patient outcomes, schedule-gap notes, interface + event history

Tabs match the live product shape: **Vault · Code Review · Archive · Office · Audit**.

**Operator & analyst guide (screenshots + procedures):** [docs/OPERATOR_GUIDE.md](docs/OPERATOR_GUIDE.md)

![Vault overview](docs/screenshots/01-vault.png)

![Code Review](docs/screenshots/02-code-review.png)

---

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5055

---

## Try the full loop

1. Open **Code Review**. Sign off a patient with no schedule gap → SOAP posts as **Draft**.
2. Click **Simulate PM Approved** → mirrored status becomes **Approved** only after confirmation.
3. Open **Office**. Resolve the Casey Nguyen schedule-gap note, then return to Code Review and sign off.
4. Check **Archive** and **Audit** for outcomes and interface calls.

---

## Architecture

```
Synthetic multi-patient packet
        |
        v
   Vault (original + shared day sheet)
        |
        v
  Parse -> patient work items (JSON)
        |
        v
  Code Review (medical coding + human signoff)
        |
        v
  Mock PM/EHR (SOAP CreatePatient/CreateEncounter + REST status)
        |
        v
  Fail-safe Draft/Approved sync
        |
        v
  Archive + Office notes + Audit events
```

Details: [docs/OPERATOR_GUIDE.md](docs/OPERATOR_GUIDE.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/HIPAA_CONTROLS.md](docs/HIPAA_CONTROLS.md)

---

## Tests

```bash
python -m pytest tests -q
```

Covers payload validation, approval gate, and fail-safe sync behavior.

---

## Honest boundaries

- This is a **workflow demo** of production Command Center at ClearBilling Services, not a visual clone.
- It is **not** the production deployment and contains no live PHI.
- Interface calls hit an in-process mock PM/EHR API, not a vendor sandbox.
- Built to show systems-analyst work: specs, medical coding gates, interface testing, signoff, HIPAA-minded controls, and production defect handling.

---

## License

MIT - portfolio / educational use.
