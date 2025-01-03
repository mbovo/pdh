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
import json
import pytest
import io
from unittest.mock import patch, MagicMock
from pdh.rules import exec, __load_data_from_stdin, rule, chain

def test_exec():
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "error")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        response = exec("ls")
        assert response.stdout == "output"
        assert response.stderr == "error"
        assert response.rc == 0

def test_load_data_from_stdin():
    test_data = {"key": "value"}
    with patch("sys.stdin", io.StringIO(json.dumps(test_data))):
        assert __load_data_from_stdin() == test_data

@pytest.fixture
def dummy_rule():
    @rule
    def test_rule(alerts, pagerduty, Filters, Transformations):
        return {"processed": True, "alerts": alerts}
    return test_rule

def test_rule_decorator(dummy_rule):
    test_input = {"key": "value"}
    with patch("pdh.rules.__load_data_from_stdin", return_value=test_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = dummy_rule()
            assert json.loads(mock_stdout.getvalue()) == {"processed": True, "alerts": test_input}
            assert result == {"processed": True, "alerts": test_input}


# Mock classes and functions
class MockIncidents:
    def apply_single(self, incs, path):
        # Mock behavior based on path for testing
        if path == "path_with_output":
            return {"output": ["success"]}
        elif path == "path_with_stderr":
            return {"stderr": ["error"]}
        else:
            return {}

@pytest.fixture
def mock_incidents():
    return MockIncidents()

@pytest.fixture
def mock_api():
    with patch("pdh.rules.Incidents", return_value=MockIncidents()) as mock:
        yield mock

@pytest.fixture
def mock_config_load():
    with patch("pdh.rules.config.load_and_validate", return_value={"some": "config"}) as mock:
        yield mock


@pytest.mark.skip("Not working without a valid config")
def test_chain_without_provided_pd(mock_api):
    incs = ["incident1", "incident2"]
    path = "path_with_output"
    result = chain(incs, path)
    assert result == ["success"]
