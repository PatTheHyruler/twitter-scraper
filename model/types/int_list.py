from typing import List

from sqlalchemy import types


class IntList(types.TypeDecorator):
    impl = types.JSON
    cache_ok = True

    def process_literal_param(self, value, dialect):
        pass

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, list):
            raise RuntimeError(f"Expected object of type List, but got {value.__class__.__name__}")

        items = []

        for item in value:
            if not isinstance(item, int):
                raise RuntimeError(f"Expected object of type int, but got {item.__class__.__name__}")

            items.append(str(item))

        return ",".join(items)

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        return [int(item) for item in value.split(",")]

    @property
    def python_type(self):
        return List[int]
