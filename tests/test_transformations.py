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

from pdh import Transformations
import datetime

apple = {
    "intfield": 42,
    "strfield": "apple",
    "afield": "this is apple",
    "bestbefore": (datetime.datetime.now() - datetime.timedelta(days=22, hours=12, minutes=22)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    'assignments': [
            {
                'at': '2024-06-24T08:04:18Z',
                'assignee': {
                    'id': 'USERID01',
                    'type': 'user_reference',
                    'summary': 'Rakhi',
                    'self': 'https://api.pagerduty.com/users/USERID01',
                    'html_url': 'https://sysdig.pagerduty.com/users/USERID01'
                }
            }
        ],
}
kiwi = {
    "intfield": 8,
    "strfield": "kiwi",
    "afield": "this is kiwi",
    "bestbefore": (datetime.datetime.now() - datetime.timedelta(days=2, hours=4, minutes=12)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        'assignments': [
            {
                'at': '2024-06-23T09:04:10Z',
                'assignee': {
                    'id': 'USERID02',
                    'type': 'user_reference',
                    'summary': 'Prasanna',
                    'self': 'https://api.pagerduty.com/users/USERID02',
                    'html_url': 'https://sysdig.pagerduty.com/users/USERID02'
                }
            }
        ],
}
orange = {
    "intfield": 23,
    "strfield": "orange",
    "afield": "this is orange",
    "dictfield" : {"inside": "worm"},
    "bestbefore": (datetime.datetime.now() - datetime.timedelta(days=175, hours=20, minutes=23)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    'assignments': [
            {
                'at': '2024-06-15T08:12:24Z',
                'assignee': {
                    'id': 'USER03',
                    'type': 'user_reference',
                    'summary': 'Michele',
                    'self': 'https://api.pagerduty.com/users/USER03',
                    'html_url': 'https://sysdig.pagerduty.com/users/USER03'
                }
            }
        ],
}

ilist = [apple, kiwi, orange]

def test_extract_date()-> None:
    t = Transformations.extract_date("bestbefore")
    result = Transformations.apply(ilist, {"bestbefore": t})
    assert len(result) == 3


def test_extract_field() -> None:
    t: dict = {"newfield": Transformations.extract("strfield")}
    result = Transformations.apply(ilist, t)
    assert len(result) == 3
    assert result[0]["newfield"] == "apple"
    assert result[1]["newfield"] == "kiwi"
    assert result[2]["newfield"] == "orange"

def test_extract_field_change() -> None:
    t: dict = {"newfield": Transformations.extract_change("strfield", change_map={"apple": "banana"})}
    result = Transformations.apply(ilist, t)
    assert len(result) == 3
    assert result[0]["newfield"] == "banana"
    assert result[1]["newfield"] == "kiwi"
    assert result[2]["newfield"] == "orange"


def test_extract_path():
    t: dict = {"newfield": Transformations.extract("dictfield.inside", "-x-")}
    result = Transformations.apply(ilist, t)
    assert len(result) == 3
    assert result[0]["newfield"] == "-x-"
    assert result[1]["newfield"] == "-x-"
    assert result[2]["newfield"] == "worm"

def test_extract_assignees() -> None:
    t: dict = {"newfield": Transformations.extract_assignees("magenta")}
    result = Transformations.apply(ilist, t)
    assert len(result) == 3
    assert result[0]["newfield"] == "[magenta]Rakhi[/magenta]"
    assert result[1]["newfield"] == "[magenta]Prasanna[/magenta]"
    assert result[2]["newfield"] == "[magenta]Michele[/magenta]"
