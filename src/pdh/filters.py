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
        if type(regexp) is str:
            regexp = re.compile(regexp)

        def f(item: dict) -> bool:
            if regexp.search(item[field]):
                return True
            return False

        return f

    def objects(objects: list, transformations: dict = None, filters: list = []) -> list:
        """Given a list of objects, apply every transformations and filters on it, return the new filtered list
        Transformations is a dict of "key": func(item) where key is the destination key and func(item) the
                        function to used to extract values from the original list (see Transformation class)
        Filters is a list of functions in the form f(item:Any)->bool the item will be in the returned list
                        if the function returns True
        """
        ret = list()
        for obj in objects:
            if transformations is not None:
                item = {}
                for path, func in transformations.items():
                    item[path] = func(obj)
                ret.append(item)
            else:
                ret.append(obj)
        for filter_func in filters:
            ret = [o for o in filter(filter_func, ret)]

        return ret
