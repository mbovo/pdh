import pytest
from pytest_mock import MockerFixture
import json

from requests.models import Response
from pdh import pd


@pytest.fixture
def config() -> dict():
    # This is the test token from https://developer.pagerduty.com/api-reference
    return {"apikey": "y_NbAkKc66ryYTWUXYEu", "email": "user@domain.tld", "uid": "PXCT22H"}


@pytest.fixture
def users(mocker: MockerFixture, config) -> pd.Incidents:
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

    def fake_get(addr: str, **kwargs) -> Response:
        return Response()

    def fake_post(addr: str, json: dict) -> Response:
        return Response()

    def fake_rput(*argv, **kwargs) -> Response:
        return Response()

    mocker.patch("pdpyras.APISession.list_all", side_effect=fake_list_incident)
    mocker.patch("pdpyras.APISession.rget", side_effect=fake_get_incident)
    mocker.patch("pdpyras.APISession.rput", side_effect=fake_put_incident)
    mocker.patch("pdpyras.APISession.get", side_effect=fake_get)
    mocker.patch("pdpyras.APISession.post", side_effect=fake_post)
    return pd.Users(config)


def test_list_users(users: pd.Users, config):
    assert False


def test_get_users(users: pd.Users):
    assert False


def test_search(users: pd.Users):
    assert False


def test_filter(users: pd.Users):
    assert False


def test_userIDs(users: pd.Users):
    assert False


def test_userID_by_mail(users: pd.Users):
    assert False


def test_userID_by_name(users: pd.Users):
    assert False
