"""Mock practice-management / EHR interface (SOAP-shaped + REST).

Demonstrates WSDL-style field mapping, CreatePatient + CreateEncounter,
and fail-safe status sync without calling any real vendor API.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


REQUIRED_PATIENT_FIELDS = ("legal_name", "dob", "mrn_synthetic")
REQUIRED_ENCOUNTER_FIELDS = (
    "legal_name",
    "dob",
    "dos",
    "cpt",
    "mrn_synthetic",
    "laterality",
    "procedure",
)


class InterfaceValidationError(ValueError):
    pass


class MockPracticeManagementAPI:
    """In-memory stand-in for a PM/EHR SOAP + REST interface."""

    def __init__(self) -> None:
        self.patients: dict[str, dict[str, Any]] = {}
        self.encounters: dict[str, dict[str, Any]] = {}
        self.call_log: list[dict[str, Any]] = []

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _log(self, method: str, work_item_id: str, result: str) -> None:
        self.call_log.append(
            {
                "at": self._now(),
                "method": method,
                "work_item_id": work_item_id,
                "result": result,
            }
        )

    def validate_payload(self, payload: dict[str, Any], required: tuple[str, ...] | None = None) -> list[str]:
        fields = required or REQUIRED_ENCOUNTER_FIELDS
        return [f for f in fields if not payload.get(f)]

    def create_patient_soap(self, work_item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        missing = self.validate_payload(payload, REQUIRED_PATIENT_FIELDS)
        if missing:
            raise InterfaceValidationError(
                f"CreatePatient missing required fields: {', '.join(missing)}"
            )

        soap_body = {
            "CreatePatient": {
                "PatientName": payload["legal_name"],
                "DateOfBirth": payload["dob"],
                "MRN": payload["mrn_synthetic"],
                "ExternalWorkItemId": work_item_id,
            }
        }
        record = {
            "patient_id": f"PAT-{work_item_id}",
            "work_item_id": work_item_id,
            "soap_body": soap_body,
            "created_at": self._now(),
        }
        self.patients[work_item_id] = record
        self._log("SOAP:CreatePatient", work_item_id, record["patient_id"])
        return deepcopy(record)

    def create_encounter_soap(self, work_item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Simulate a SOAP CreateEncounter call with WSDL-mapped fields."""
        missing = self.validate_payload(payload)
        if missing:
            raise InterfaceValidationError(
                f"WSDL-mapped payload missing required fields: {', '.join(missing)}"
            )

        if work_item_id not in self.patients:
            self.create_patient_soap(work_item_id, payload)

        soap_body = {
            "CreateEncounter": {
                "PatientName": payload["legal_name"],
                "DateOfBirth": payload["dob"],
                "DateOfService": payload["dos"],
                "CPTCode": payload["cpt"],
                "ASAClass": payload.get("asa") or "",
                "MRN": payload["mrn_synthetic"],
                "Laterality": payload["laterality"],
                "ProcedureDescription": payload["procedure"],
                "Facility": payload.get("facility") or "",
                "Clinician": payload.get("clinician") or "",
                "ExternalWorkItemId": work_item_id,
                "PatientId": self.patients[work_item_id]["patient_id"],
            }
        }

        record = {
            "interface_id": f"PM-{work_item_id}",
            "work_item_id": work_item_id,
            "status": "Draft",
            "payload": deepcopy(payload),
            "soap_body": soap_body,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.encounters[work_item_id] = record
        self._log("SOAP:CreateEncounter", work_item_id, "Draft")
        return deepcopy(record)

    def approve_encounter(self, work_item_id: str) -> dict[str, Any]:
        if work_item_id not in self.encounters:
            raise KeyError(f"Unknown encounter for work item {work_item_id}")
        self.encounters[work_item_id]["status"] = "Approved"
        self.encounters[work_item_id]["updated_at"] = self._now()
        self._log("REST:SetEncounterStatus", work_item_id, "Approved")
        return deepcopy(self.encounters[work_item_id])

    def get_encounter_status(self, work_item_id: str) -> str | None:
        rec = self.encounters.get(work_item_id)
        return None if rec is None else rec["status"]

    def sync_status_failsafe(self, work_item_id: str, local_status: str) -> dict[str, Any]:
        """Mirror remote status. Never force Approved without interface confirmation."""
        remote = self.get_encounter_status(work_item_id)
        if remote is None:
            return {
                "work_item_id": work_item_id,
                "local_status": local_status,
                "remote_status": None,
                "mirrored_status": local_status,
                "forced_approved": False,
                "note": "No remote encounter yet",
            }

        mirrored = remote
        # Explicit fail-safe: local wishful Approved does not override remote Draft
        if local_status == "Approved" and remote != "Approved":
            mirrored = remote

        return {
            "work_item_id": work_item_id,
            "local_status": local_status,
            "remote_status": remote,
            "mirrored_status": mirrored,
            "forced_approved": False,
            "note": "Fail-safe sync applied",
        }

    def clear(self) -> None:
        self.patients.clear()
        self.encounters.clear()
        self.call_log.clear()
