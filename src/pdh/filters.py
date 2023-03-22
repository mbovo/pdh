#
# This file is part of the pdh (https://github.com/mbovo/pdh).
# Copyright (c) 2020-2023 Manuel Bovo.
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
from typing import List


class Filter(object):
    """
    Filter is a collection of methods to functions to filter out items from an iterator,
    useful when used in conjunction with filter()
    """

    def le(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] <= value:
                return True
            return False

        return f

    def ge(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] >= value:
                return True
            return False

        return f

    def lt(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] < value:
                return True
            return False

        return f

    def gt(field: str, value: int):
        def f(item: dict) -> bool:
            if item[field] > value:
                return True
            return False

        return f

    def inList(field: str, listOfValues: List[str]):
        def f(item: dict) -> bool:
            if item[field] in listOfValues:
                return True
            return False

        return f

    def inStr(field: str, value: str):
        def f(item: dict) -> bool:
            if value.lower() in item[field].lower():
                return True
            return False

        return f

    def ieq(field: str, value: str):
        def f(item: dict) -> bool:
            if item[field].lower() == value.lower():
                return True
            return False

        return f

    def eq(field: str, value: str):
        def f(item: dict) -> bool:
            if item[field] == value:
                return True
            return False

        return f

    def regexp(field: str, regexp):
        """
        This is a filters operating on regular expression

            Parameters:
                field (str): Any dictionary field on which operate
                regexp (str or regexp): The regular expression you would validate

            Returns:
                True if when regexp is found, false otherwise

        """
        if type(regexp) is str:
            regexp = re.compile(regexp)

        def f(item: dict) -> bool:
            if regexp.search(item[field]):
                return True
            return False

        return f

    def not_regexp(field: str, regexp):
        """
        This is a filters operating on regular expression

            Parameters:
                field (str): Any dictionary field on which operate
                regexp (str or regexp): The regular expression you would validate

            Returns:
                False if when regexp is found, True otherwise

        """
        if type(regexp) is str:
            regexp = re.compile(regexp)

        def f(item: dict) -> bool:
            if regexp.search(item[field]):
                return False
            return True

        return f

    def do(objects: list, transformations: dict = None, filters: list = [], preserve : bool = False) -> list:
        """Given a list of objects, apply every transformations and filters on it, return the new filtered list
        Transformations is a dict of "key": func(item) where key is the destination key and func(item) the
                        function to used to extract values from the original list (see Transformation class)
        Filters is a list of functions in the form f(item:Any)->bool the item will be in the returned list
                        if the function returns True
        """
        ret = list()
        for obj in objects:
            if transformations is not None:
                if preserve:
                    item = obj
                else:
                    item = {}
                for path, func in transformations.items():
                    item[path] = func(obj)
                ret.append(item)
            else:
                ret.append(obj)
        for filter_func in filters:
            ret = [o for o in filter(filter_func, ret)]

        return ret
