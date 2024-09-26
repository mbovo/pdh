
#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2024 Manuel Bovo.
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
import pytest
from unittest.mock import patch, MagicMock
from pdh.core import PDH
from pdh.config import Config

@pytest.fixture
def mock_config():
    return MagicMock(spec=Config)

@pytest.fixture
def mock_users():
    with patch('pdh.core.Users') as mock:
        yield mock

def test_list_user_default_fields(mock_config, mock_users):
    result = PDH.list_user(mock_config, 'raw')
    mock_users.assert_called_once()
    assert result is True

def test_list_user_with_fields_list(mock_config, mock_users):
    fields = ["id", "email"]
    result = PDH.list_user(mock_config, 'raw', fields=fields)
    mock_users.assert_called_once()
    assert result is True
