#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2025 Manuel Bovo.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from typing import Dict, List
import pytest
from pytest_mock import MockerFixture
import json

from requests.models import Response
from pdh import pd
from pdh.config import Config


class FakePD(object):

    @staticmethod
    def list_all(*args, **kwargs) -> List:
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

    @staticmethod
    def iter_all(*args, **kwargs) -> List:
        loaded = []
        if args[1] == "users":
            with open("tests/users_list.json", "r") as f:
                loaded = json.load(f)
        return loaded

    @staticmethod
    def put_incident(addr: str, json: list):
        return json

    @staticmethod
    def get(addr: str, **kwargs) -> Response:
        return Response()

    @staticmethod
    def post(addr: str, json: dict) -> Response:
        return Response()

    @staticmethod
    def rput(*argv, **kwargs) -> Response:
        return Response()

    @staticmethod
    def rget(*argv, **kawargs) -> List:
        loaded = []
        ret = []
        if "users" in argv[0]:
            uid = argv[0].replace("/users/", "")
            with open("tests/users_list.json", "r") as f:
                loaded = json.load(f)
                for u in loaded:
                    if u["id"] == uid:
                        ret.append(u)
        if "incidents" in argv[0]:
            id = argv[0].replace("/incidents/", "")
            with open("tests/incidents_list.json", "r") as f:
                loaded = json.load(f)
            for i in loaded:
                if i["id"] == id:
                    ret.append(i)

        return ret


@pytest.fixture
def config() -> Config:
    # This is the test token from https://developer.pagerduty.com/api-reference
    c = Config()
    c.from_dict({"apikey": "y_NbAkKc66ryYTWUXYEu",
                "email": "user@domain.tld", "uid": "PXCT22H"})
    return c


@pytest.fixture
def incidents(mocker: MockerFixture, config: Config) -> pd.Incidents:
    mocker.patch("pagerduty.RestApiV2Client.iter_all",
                 side_effect=FakePD.iter_all)
    mocker.patch("pagerduty.RestApiV2Client.rget", side_effect=FakePD.rget)
    mocker.patch("pagerduty.RestApiV2Client.list_all",
                 side_effect=FakePD.list_all)
    mocker.patch("pagerduty.RestApiV2Client.rput", side_effect=FakePD.rput)
    mocker.patch("pagerduty.RestApiV2Client.get", side_effect=FakePD.get)
    mocker.patch("pagerduty.RestApiV2Client.post", side_effect=FakePD.post)
    return pd.PagerDuty(config).incidents


@pytest.fixture
def users(mocker: MockerFixture, config: Config) -> pd.Users:
    mocker.patch("pagerduty.RestApiV2Client.iter_all",
                 side_effect=FakePD.iter_all)
    mocker.patch("pagerduty.RestApiV2Client.rget", side_effect=FakePD.rget)
    mocker.patch("pagerduty.RestApiV2Client.list_all",
                 side_effect=FakePD.list_all)
    mocker.patch("pagerduty.RestApiV2Client.rput", side_effect=FakePD.rput)
    mocker.patch("pagerduty.RestApiV2Client.get", side_effect=FakePD.get)
    mocker.patch("pagerduty.RestApiV2Client.post", side_effect=FakePD.post)
    return pd.PagerDuty(config).users


def test_list_incidents(incidents: pd.Incidents, config: Dict):
    incs = incidents.list()
    assert incs is not None
    assert len(incs) > 0
    assert incs[0]["assignments"][0]["assignee"]["id"] == config["uid"]


def test_list_my_incidents(incidents: pd.Incidents, config: Dict):
    incs = incidents.mine()
    assert incs is not None
    assert len(incs) > 0
    for i in incs:
        assert i["assignments"][0]["assignee"]["id"] == config["uid"]


def test_get_incident(incidents: pd.Incidents):
    inc = incidents.get("Q0VVEEB5HX4U06")
    assert inc is not None
    assert len(inc) > 0
    assert inc[0]["id"] == "Q0VVEEB5HX4U06"


def test_ack(incidents: pd.Incidents):
    inc = incidents.get("Q0VVEEB5HX4U06")
    assert inc is not None
    incidents.ack(inc)
    assert inc[0]["status"] == pd.STATUS_ACK


def test_resolve(incidents: pd.Incidents):
    inc = incidents.get("Q0VVEEB5HX4U06")
    assert inc is not None
    incidents.resolve(inc)
    assert inc[0]["status"] == pd.STATUS_RESOLVED


def test_snooze(incidents: pd.Incidents):
    inc = incidents.get("Q0VVEEB5HX4U06")
    assert inc is not None
    incidents.snooze(inc, 6000)
    # TODO: verify


def test_reassign(incidents: pd.Incidents, config: Dict):
    inc = incidents.get("Q0VVEEB5HX4U06")
    assert inc is not None
    # Reassign to me
    incidents.reassign(inc, uids=["1P3E4F"])
    # TODO: verify


# def test_list_users(users: pd.Users, config):
#     assert False


# def test_get_users(users: pd.Users):
#     assert False


# def test_search(users: pd.Users):
#     assert False


# def test_filter(users: pd.Users):
#     assert False


# def test_userIDs(users: pd.Users):
#     assert False


# def test_userID_by_mail(users: pd.Users):
#     assert False


# def test_userID_by_name(users: pd.Users):
#     assert False
