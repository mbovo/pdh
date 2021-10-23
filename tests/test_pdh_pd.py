import pytest
from pytest_mock import MockerFixture

from pdh import pd


@pytest.fixture
def config() -> dict():
    # This is the test token from https://developer.pagerduty.com/api-reference
    return {"apikey": "y_NbAkKc66ryYTWUXYEu", "email": "user@domain.tld", "uid": "UID123"}


@pytest.fixture
def pagerduty(mocker: MockerFixture, config) -> pd.PD:
    def fake_list_incident(*args, **kwargs):
        return [
            {
                "id": "PT4KHLK",
                "type": "incident",
                "summary": "[#1234] The server is on fire.",
                "self": "https://api.pagerduty.com/incidents/PT4KHLK",
                "html_url": "https://subdomain.pagerduty.com/incidents/PT4KHLK",
                "incident_number": 1234,
                "created_at": "2015-10-06T21:30:42Z",
                "status": "resolved",
                "title": "The server is on fire.",
                "incident_key": "baf7cf21b1da41b4b0221008339ff357",
                "service": {
                    "id": "PIJ90N7",
                    "type": "service_reference",
                    "summary": "My Mail Service",
                    "self": "https://api.pagerduty.com/services/PIJ90N7",
                    "html_url": "https://subdomain.pagerduty.com/services/PIJ90N7",
                },
                "priority": {
                    "id": "P53ZZH5",
                    "type": "priority_reference",
                    "summary": "P2",
                    "self": "https://api.pagerduty.com/priorities/P53ZZH5",
                },
                "assigned_via": "escalation_policy",
                "assignments": [],
                "acknowledgements": [],
                "last_status_change_at": "2015-10-06T21:38:23Z",
                "last_status_change_by": {
                    "id": "PXPGF42",
                    "type": "user_reference",
                    "summary": "Earline Greenholt",
                    "self": "https://api.pagerduty.com/users/PXPGF42",
                    "html_url": "https://subdomain.pagerduty.com/users/PXPGF42",
                },
                "first_trigger_log_entry": {
                    "id": "Q02JTSNZWHSEKV",
                    "type": "trigger_log_entry_reference",
                    "summary": "Triggered through the API",
                    "self": "https://api.pagerduty.com/log_entries/Q02JTSNZWHSEKV?incident_id=PT4KHLK",
                    "html_url": "https://subdomain.pagerduty.com/incidents/PT4KHLK/log_entries/Q02JTSNZWHSEKV",
                },
                "escalation_policy": {
                    "id": "PT20YPA",
                    "type": "escalation_policy_reference",
                    "summary": "Another Escalation Policy",
                    "self": "https://api.pagerduty.com/escalation_policies/PT20YPA",
                    "html_url": "https://subdomain.pagerduty.com/escalation_policies/PT20YPA",
                },
                "teams": [
                    {
                        "id": "PQ9K7I8",
                        "type": "team_reference",
                        "summary": "Engineering",
                        "self": "https://api.pagerduty.com/teams/PQ9K7I8",
                        "html_url": "https://subdomain.pagerduty.com/teams/PQ9K7I8",
                    }
                ],
                "urgency": "high",
                "conference_bridge": {
                    "conference_number": "+1-415-555-1212,,,,1234#",
                    "conference_url": "https://example.com/acb-123",
                },
            }
        ]

    mocker.patch("pdh.pd.PD.list_incidents", return_value=fake_list_incident())
    mocker.patch("pdh.pd.PD.get_incident", return_value=fake_list_incident())
    return pd.PD(config)


def test_list_incidents(pagerduty):
    incs = pagerduty.list_incidents()
    assert incs is not None
    assert len(incs) > 0


def test_list_my_incidents(pagerduty):
    incs = pagerduty.list_my_incidents()
    assert incs is not None
    assert len(incs) > 0


def test_get_incident(pagerduty):
    inc = pagerduty.get_incident("PT4KHLK")
    assert inc is not None
    assert len(inc) > 0


def test_ack(pagerduty):
    inc = pagerduty.get_incident("PT4KHLK")
    assert inc is not None
    inc = pagerduty.ack(inc[0])
    assert inc["status"] == "acknowledged"


def test_resolve(pagerduty):
    inc = pagerduty.get_incident("PT4KHLK")
    assert inc is not None
    inc = pagerduty.resolve(inc[0])
    assert inc["status"] == "resolved"
