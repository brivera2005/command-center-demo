from middleware.mock_pm_api import InterfaceValidationError, MockPracticeManagementAPI


def test_payload_validation_catches_missing_fields():
    api = MockPracticeManagementAPI()
    missing = api.validate_payload({"legal_name": "Alex Rivera"})
    assert "dob" in missing
    assert "cpt" in missing


def test_create_encounter_requires_complete_payload():
    api = MockPracticeManagementAPI()
    try:
        api.create_encounter_soap("WI-X", {"legal_name": "Alex Rivera"})
        assert False, "expected validation error"
    except InterfaceValidationError:
        pass


def test_create_patient_then_encounter_and_failsafe_sync():
    api = MockPracticeManagementAPI()
    payload = {
        "legal_name": "Alex Rivera",
        "dob": "1984-03-12",
        "dos": "2026-08-09",
        "cpt": "66984",
        "asa": "",
        "mrn_synthetic": "SYN-1",
        "laterality": "Left",
        "procedure": "Cataract",
        "facility": "Demo Eye ASC",
        "clinician": "Dr. Morgan Ellis",
    }
    patient = api.create_patient_soap("WI-1", payload)
    assert patient["patient_id"].startswith("PAT-")

    enc = api.create_encounter_soap("WI-1", payload)
    assert enc["status"] == "Draft"

    sync = api.sync_status_failsafe("WI-1", local_status="Approved")
    assert sync["remote_status"] == "Draft"
    assert sync["mirrored_status"] == "Draft"
    assert sync["forced_approved"] is False

    api.approve_encounter("WI-1")
    sync2 = api.sync_status_failsafe("WI-1", local_status="Approved")
    assert sync2["mirrored_status"] == "Approved"


def test_auto_create_patient_inside_encounter():
    api = MockPracticeManagementAPI()
    payload = {
        "legal_name": "Jordan Lee",
        "dob": "1977-11-02",
        "dos": "2026-08-09",
        "cpt": "66821",
        "mrn_synthetic": "SYN-2",
        "laterality": "Right",
        "procedure": "YAG",
    }
    enc = api.create_encounter_soap("WI-2", payload)
    assert "WI-2" in api.patients
    assert enc["status"] == "Draft"
