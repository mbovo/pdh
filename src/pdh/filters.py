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
import re
from typing import Callable, Iterator, List, Dict, Any

class Filter(object):
    """
    Filter is a collection of methods to functions to filter out items from an iterator,
    useful when used in conjunction with filter()
    """

    @staticmethod
    def le(field: str, value: int) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if the value of a specified field in a dictionary is less than or equal to a given value.

        Args:
            field (str): The key in the dictionary to compare.
            value (int): The value to compare against.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the value of the specified field is less than or equal to the given value, otherwise False.
        """
        def f(item: dict) -> bool:
            if item[field] <= value:
                return True
            return False

        return f

    @staticmethod
    def ge(field: str, value: int)-> Callable[[dict], bool]:
        """
        Creates a filter function that checks if the value of a specified field in a dictionary is greater than or equal to a given value.

        Args:
            field (str): The key in the dictionary to check.
            value (int): The value to compare against.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the value of the specified field is greater than or equal to the given value, otherwise False.
        """
        def f(item: dict) -> bool:
            if item[field] >= value:
                return True
            return False

        return f

    @staticmethod
    def lt(field: str, value: int) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if a specified field in a dictionary is less than a given value.

        Args:
            field (str): The key in the dictionary to compare.
            value (int): The value to compare against.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the specified field's value is less than the given value, otherwise False.
        """
        def f(item: dict) -> bool:
            if item[field] < value:
                return True
            return False

        return f

    @staticmethod
    def gt(field: str, value: int) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if the value of a specified field in a dictionary is greater than a given value.

        Args:
            field (str): The key in the dictionary to compare.
            value (int): The value to compare against.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the value of the specified field is greater than the given value, otherwise False.
        """
        def f(item: dict) -> bool:
            if item[field] > value:
                return True
            return False

        return f

    @staticmethod
    def inList(field: str, listOfValues: List[str]) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if the value of a specified field in a dictionary
        is within a given list of values.

        Args:
            field (str): The key in the dictionary to check.
            listOfValues (List[str]): The list of values to check against.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the
            value of the specified field is in the list of values, otherwise False.
        """
        def f(item: dict) -> bool:
            if item[field] in listOfValues:
                return True
            return False

        return f

    @staticmethod
    def inStr(field: str, value: str) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if a given value is present in the specified field of a dictionary.

        Args:
            field (str): The key in the dictionary to check.
            value (str): The value to search for within the specified field.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary as input and returns True if the value is found in the specified field, otherwise False.
        """
        def f(item: dict) -> bool:
            if value.lower() in item[field].lower():
                return True
            return False

        return f

    @staticmethod
    def ieq(field: str, value: str) -> Callable[[dict], bool]:
        """
        Creates a case-insensitive equality filter function.

        Args:
            field (str): The key in the dictionary to compare.
            value (str): The value to compare against.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the value of the specified field matches the given value (case-insensitive), otherwise False.
        """
        def f(item: dict) -> bool:
            if item[field].lower() == value.lower():
                return True
            return False

        return f

    @staticmethod
    def eq(field: str, value: Any) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if a specified field in a dictionary equals a given value.

        Args:
            field (str): The key in the dictionary to check.
            value (Any): The value to compare against the dictionary's field value.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the specified field's value equals the given value, otherwise False.
        """

        def f(item: dict) -> bool:
            if item[field] == value:
                return True
            return False

        return f

    @staticmethod
    def regexp(field: str, regexp) -> Callable[[dict], bool]:
        """
        Creates a filter function that checks if a given field in a dictionary matches a regular expression.

        Args:
            field (str): The key in the dictionary to be checked.
            regexp (str or re.Pattern): The regular expression to match against the field's value. If a string is provided, it will be compiled into a regular expression.

        Returns:
            Callable[[dict], bool]: A function that takes a dictionary and returns True if the value of the specified field matches the regular expression, otherwise False.
        """

        if type(regexp) is str:
            regexp = re.compile(regexp)

        def f(item: dict) -> bool:
            if regexp.search(item[field]):
                return True
            return False

        return f

    @staticmethod
    def not_regexp(field: str, regexp) -> Callable[[dict], bool]:
        """
        This is a filter operating on regular expressions.

            field (str): Any dictionary field on which to operate.
            regexp (str or Pattern): The regular expression to validate.

            Callable[[dict], bool]: A function that returns False if the regexp is found, True otherwise.
        """
        if type(regexp) is str:
            regexp = re.compile(regexp)

        def f(item: dict) -> bool:
            if regexp.search(item[field]):
                return False
            return True

        return f

    @staticmethod
    def apply(objects: List[Any] | List[Dict[Any, Any]] | Iterator[Any], filters: List[Callable[[Dict], Any]] = []) -> List[Any] | List[Dict[Any, Any]] | Iterator[Any]:
        """
        Filters a collection of objects.

        Args:
            objects (Iterator): An iterator of objects to be filtered and transformed.
            transformations (dict | None, optional): A dictionary where keys are paths and values are functions to transform the objects. Defaults to None.
            filters (list, optional): A list of filter functions to apply to the objects. Defaults to an empty list.

        Returns:
            list: A list of filtered objects (object for which at least one filter function returned True).
        """
        ret = objects
        for filter_func in filters:
            ret = [o for o in filter(filter_func, ret)]

        return ret
