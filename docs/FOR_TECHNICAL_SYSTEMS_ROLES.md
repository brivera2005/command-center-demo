# Command Center → Technical Systems roles

Interview-ready narrative for Director of Technical Operations work at Clear Billing Services, mapped to technical systems / healthcare payment infrastructure roles (internal tooling, secure onboarding, workflow automation, compliance-minded ops).

**Repo:** runnable sandbox of the same ops loop (synthetic data only).  
**Live product:** multi-facility anesthesia / clinical charge operations platform used daily by operators.

---

## STARS story: building Command Center

**Situation.** Off-the-shelf billing tools could not give our team one trustworthy view of packet intake, medical coding review, PM/EHR writeback, and exception holds across many practices. Manual status checks and spreadsheet handoffs were slow and error-prone under HIPAA and revenue pressure.

**Task.** As Director of Technical Operations I owned the design and delivery of **Command Center**: a single operational hub so coding, office, and leadership share one source of truth from vault upload through Archive.

**Action.**

- Architected the loop: Vault → Code Review → Interface → Archive / Office / Audit.
- Enforced human signoff before any PM/EHR write; fail-safe Draft → Approved sync only after the interface confirms.
- Built practice isolation, schedule-gap / Office holds, coding gates (CPT/ASA, laterality, identity), and durable patient identity so index drift cannot cross-wire charts.
- Used modern AI-assisted development (Cursor) to ship and harden internal automations quickly while keeping review discipline (compile checks, staged deploys, changelog).

**Result.** Operators work from one desk instead of chasing status across tools. Leadership gets live visibility into bottlenecks. The same pattern (find friction → custom system → reliable automation) is what I bring to technical systems roles that expand team capacity and protect compliance.

---

## Talking points (keep concrete)

- **Authority:** operator picks stick; AI / OCR never silently overwrites confirmed location, DOS, or providers.
- **Safety:** no write without signoff; Draft is not Approved until confirmation.
- **Exceptions:** Office / schedule gaps are owned queues, not buried logs.
- **Tenancy:** practice walls are hard rules, not preferences.
- **Build speed:** AI-assisted coding accelerates delivery; production still gets compile gates and changelog discipline.

---

## Pair with Prism

Upstream clinician intake (secure digital handoff):  
https://github.com/brivera2005/clinician-mobile-intake

Portfolio index:  
https://github.com/brivera2005/healthcare-portfolio
