"""ClearBilling Command Center Demo - sanitized clinical ops workflow app.

Public workflow sandbox of the live Command Center loop
(Vault -> Code Review -> Archive / Office / Audit) with synthetic data only.
Not the production UI or deployment - proprietary chrome stays private.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from middleware.mock_pm_api import InterfaceValidationError, MockPracticeManagementAPI

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "sample_packets.json"
DEMO_SEMVER = "1.4.0"

app = Flask(__name__)
pm = MockPracticeManagementAPI()

STATE: dict = {
    "practices": [],
    "packets": [],
    "archive": [],
    "office_notes": [],
    "events": [],
    "incidents": [],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(kind: str, message: str, meta: dict | None = None) -> None:
    STATE["events"].insert(
        0,
        {"at": _now(), "kind": kind, "message": message, "meta": meta or {}},
    )


def load_seed() -> None:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    STATE["practices"] = deepcopy(raw.get("practices", []))
    STATE["packets"] = deepcopy(raw["packets"])
    STATE["office_notes"] = deepcopy(raw.get("office_notes", []))
    STATE["archive"] = []
    STATE["events"] = []
    STATE["incidents"] = []
    _log("system", "Loaded synthetic Command Center demo packets (no real PHI).")


def find_work_item(work_item_id: str):
    for packet in STATE["packets"]:
        for patient in packet["patients"]:
            if patient["work_item_id"] == work_item_id:
                return packet, patient
    return None, None


def _counts() -> dict:
    pending = sum(
        1
        for p in STATE["packets"]
        for pt in p["patients"]
        if pt.get("review_status") == "pending"
    )
    gaps = sum(
        1
        for p in STATE["packets"]
        for pt in p["patients"]
        if pt.get("gap_flag") and pt.get("review_status") == "pending"
    )
    open_notes = sum(1 for n in STATE["office_notes"] if n.get("status") == "open")
    return {
        "pending_reviews": pending,
        "schedule_gaps": gaps,
        "open_office_notes": open_notes,
        "archive_count": len(STATE["archive"]),
        "packet_count": len(STATE["packets"]),
        "practice_count": len(STATE["practices"]),
    }


@app.get("/")
def home():
    return render_template(
        "index.html",
        semver=DEMO_SEMVER,
        practices=STATE["practices"],
        packets=STATE["packets"],
        archive=STATE["archive"],
        office_notes=STATE["office_notes"],
        events=STATE["events"][:30],
        incidents=STATE["incidents"][:15],
        call_log=pm.call_log[-20:][::-1],
        counts=_counts(),
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "app": "ClearBilling Command Center Demo",
            "semver": DEMO_SEMVER,
            "phi_mode": "synthetic_only",
            **_counts(),
        }
    )


@app.post("/api/review/<work_item_id>/approve")
def approve_work_item(work_item_id: str):
    packet, patient = find_work_item(work_item_id)
    if patient is None:
        return jsonify({"ok": False, "error": "Work item not found"}), 404
    if patient.get("review_status") != "pending":
        return jsonify({"ok": False, "error": "Work item already reviewed"}), 400
    if patient.get("gap_flag"):
        return jsonify(
            {
                "ok": False,
                "error": "Schedule gap still open. Resolve Office note / attach charge before approve.",
            }
        ), 400

    body = request.get_json(silent=True) or {}
    for field in ("cpt", "asa", "laterality", "procedure", "dob"):
        if field in body and body[field] is not None:
            patient[field] = str(body[field]).strip()

    payload = {
        "legal_name": patient["legal_name"],
        "dob": patient["dob"],
        "dos": patient["dos"],
        "cpt": patient["cpt"],
        "asa": patient.get("asa") or "",
        "mrn_synthetic": patient["mrn_synthetic"],
        "laterality": patient["laterality"],
        "procedure": patient["procedure"],
        "facility": patient.get("facility") or "",
        "clinician": patient.get("clinician") or "",
    }

    try:
        remote = pm.create_encounter_soap(work_item_id, payload)
    except InterfaceValidationError as exc:
        incident = {
            "at": _now(),
            "severity": "interface_validation",
            "work_item_id": work_item_id,
            "detail": str(exc),
            "tier": "tier-2",
        }
        STATE["incidents"].insert(0, incident)
        _log("incident", f"Interface validation failed for {work_item_id}", incident)
        return jsonify({"ok": False, "error": str(exc)}), 400

    patient["review_status"] = "approved_local"
    patient["interface_id"] = remote["interface_id"]
    patient["remote_status"] = remote["status"]

    sync = pm.sync_status_failsafe(work_item_id, local_status="Approved")
    patient["mirrored_status"] = sync["mirrored_status"]

    archive_row = {
        "work_item_id": work_item_id,
        "packet_id": packet["packet_id"],
        "practice_id": packet["practice_id"],
        "practice_name": packet.get("practice_name", packet["practice_id"]),
        "legal_name": patient["legal_name"],
        "cpt": patient["cpt"],
        "asa": patient.get("asa") or "",
        "vault_ref": packet["original_vault_ref"],
        "shared_day_sheet": packet.get("shared_day_sheet", False),
        "interface_id": remote["interface_id"],
        "remote_status": remote["status"],
        "mirrored_status": sync["mirrored_status"],
        "approved_at": _now(),
    }
    STATE["archive"].insert(0, archive_row)
    _log(
        "approve",
        f"Operator signed off {work_item_id}; CreatePatient + CreateEncounter -> {remote['status']}",
        archive_row,
    )
    return jsonify({"ok": True, "remote": remote, "sync": sync, "archive": archive_row})


@app.post("/api/review/<work_item_id>/hold")
def hold_work_item(work_item_id: str):
    packet, patient = find_work_item(work_item_id)
    if patient is None:
        return jsonify({"ok": False, "error": "Work item not found"}), 404
    body = request.get_json(silent=True) or {}
    reason = (body.get("reason") or "Held for coding / missing doc").strip()
    patient["review_status"] = "held"
    note = {
        "id": f"NOTE-{work_item_id}",
        "packet_id": packet["packet_id"],
        "patient": patient["legal_name"],
        "kind": "hold",
        "message": reason,
        "status": "open",
    }
    STATE["office_notes"].insert(0, note)
    _log("hold", f"Held {work_item_id}: {reason}", note)
    return jsonify({"ok": True, "note": note})


@app.post("/api/review/<work_item_id>/mark-remote-approved")
def mark_remote_approved(work_item_id: str):
    """Simulate PM/EHR approving the charge, then fail-safe sync."""
    packet, patient = find_work_item(work_item_id)
    if patient is None:
        return jsonify({"ok": False, "error": "Work item not found"}), 404
    if work_item_id not in pm.encounters:
        return jsonify({"ok": False, "error": "Approve locally first to create remote encounter"}), 400

    remote = pm.approve_encounter(work_item_id)
    sync = pm.sync_status_failsafe(work_item_id, local_status="Approved")
    patient["remote_status"] = remote["status"]
    patient["mirrored_status"] = sync["mirrored_status"]

    for row in STATE["archive"]:
        if row["work_item_id"] == work_item_id:
            row["remote_status"] = remote["status"]
            row["mirrored_status"] = sync["mirrored_status"]
            break

    _log(
        "sync",
        f"Remote Approved confirmed for {work_item_id}; mirrored_status={sync['mirrored_status']}",
        sync,
    )
    return jsonify({"ok": True, "remote": remote, "sync": sync})


@app.post("/api/office/<note_id>/resolve")
def resolve_office_note(note_id: str):
    for note in STATE["office_notes"]:
        if note["id"] == note_id:
            note["status"] = "resolved"
            # Clear matching schedule-gap flag so approve can proceed
            for packet in STATE["packets"]:
                if packet["packet_id"] != note.get("packet_id"):
                    continue
                for patient in packet["patients"]:
                    if patient["legal_name"] == note.get("patient") and patient.get("gap_flag"):
                        patient["gap_flag"] = False
                        patient["schedule_note"] = (
                            "Gap cleared by Office; charge attached (demo). Ready for coding signoff."
                        )
            _log("office", f"Resolved Office note {note_id}")
            return jsonify({"ok": True, "note": note})
    return jsonify({"ok": False, "error": "Note not found"}), 404


@app.post("/api/reset")
def reset_demo():
    load_seed()
    pm.clear()
    return jsonify({"ok": True, "semver": DEMO_SEMVER})


@app.get("/api/state")
def full_state():
    return jsonify(
        {
            "semver": DEMO_SEMVER,
            "practices": STATE["practices"],
            "packets": STATE["packets"],
            "archive": STATE["archive"],
            "office_notes": STATE["office_notes"],
            "events": STATE["events"],
            "incidents": STATE["incidents"],
            "interface_log": pm.call_log,
            "counts": _counts(),
        }
    )


load_seed()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=True)
