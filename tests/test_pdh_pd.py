import pytest
from pdh import pd


@pytest.fixture
def config() -> dict():
    return {"apikey": "y_NbAkKc66ryYTWUXYEu", "email": "user@domain.tld", "uid": "UID123"}


@pytest.fixture
def pagerduty(config) -> pd.PD:
    return pd.PD(config)


def test_list_incidents(pagerduty):
    incs = pagerduty.list_incidents()
    assert incs is not None


def test_list_my_incidents(pagerduty):
    incs = pagerduty.list_my_incidents()
    assert incs is not None


def get_incident(pagerduty):
    inc = pagerduty.get_incident("Q345LX")
    assert inc is not None


def ack(pagerduty):
    inc = pagerduty.ack("Q345LX")
    assert inc is not None


def resolve(pagerduty):
    inc = pagerduty.resolve("Q345LX")
    assert inc is not None
