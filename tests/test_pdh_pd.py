import pytest
from pytest_mock import MockerFixture
import json
from pdh import pd


@pytest.fixture
def config() -> dict():
    # This is the test token from https://developer.pagerduty.com/api-reference
    return {"apikey": "y_NbAkKc66ryYTWUXYEu", "email": "user@domain.tld", "uid": "PXCT22H"}


@pytest.fixture
def pagerduty(mocker: MockerFixture, config) -> pd.Incidents:
    def fake_list_incident(*args, **kwargs):
        ret = []
        loaded = []
        with open("tests/incidents_list.json", "r") as f:
            loaded = json.load(f)

        if "user_ids[]" in kwargs["params"]:
            for i in ret:
                for assignments in i["assignments"]:
                    if assignments["assignee"]["id"] in kwargs["params"]["user_ids[]"]:
                        ret.append(i)

        if "statuses[]" in kwargs["params"]:
            for i in loaded:
                if i["status"] in kwargs["params"]["statuses[]"]:
                    ret.append(i)
        if "urgencies[]" in kwargs["params"]:
            for i in loaded:
                if i["urgency"] in kwargs["params"]["urgencies[]"]:
                    ret.append(i)

        return ret

    def fake_get_incident(addr: str):
        id = addr.replace("/incidents/", "")
        loaded = []
        ret = []
        with open("tests/incidents_list.json", "r") as f:
            loaded = json.load(f)
        for i in loaded:
            if i["id"] == id:
                ret.append(i)
        return ret

    def fake_put_incident(addr: str, json: list):
        return json

    mocker.patch("pdpyras.APISession.list_all", side_effect=fake_list_incident)
    mocker.patch("pdpyras.APISession.rget", side_effect=fake_get_incident)
    mocker.patch("pdpyras.APISession.rput", side_effect=fake_put_incident)
    # mocker.patch("pdh.pd.Incidents.mine", return_value=fake_list_incident())
    # mocker.patch("pdh.pd.Incidents.get", return_value=fake_list_incident())
    # mocker.patch("pdh.pd.Incidents.bulk_update", return_value=fake_bulk_update())
    # mocker.patch("pdh.pd.Incidents.update", return_value=fake_bulk_update())
    return pd.Incidents(config)


def test_list_incidents(pagerduty, config):
    incs = pagerduty.list()
    assert incs is not None
    assert len(incs) > 0
    assert incs[0]["assignments"][0]["assignee"]["id"] == config["uid"]


def test_list_my_incidents(pagerduty, config):
    incs = pagerduty.mine()
    assert incs is not None
    assert len(incs) > 0
    for i in incs:
        assert i["assignments"][0]["assignee"]["id"] == config["uid"]


def test_get_incident(pagerduty):
    inc = pagerduty.get("Q0VVEEB5HX4U06")
    assert inc is not None
    assert len(inc) > 0
    assert inc[0]["id"] == "Q0VVEEB5HX4U06"


def test_ack(pagerduty):
    inc = pagerduty.get("Q0VVEEB5HX4U06")
    assert inc is not None
    inc = pagerduty.ack(inc[0]["id"])
    assert inc[0]["status"] == "acknowledged"


def test_resolve(pagerduty):
    inc = pagerduty.get("Q0VVEEB5HX4U06")
    assert inc is not None
    inc = pagerduty.resolve(inc[0]["id"])
    assert inc["status"] == "resolved"
