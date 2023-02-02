from typing import Dict, Type, TypeVar, List


def get_class_fields(cls) -> Dict:
    fields = {}

    for var in cls.__dict__.keys():
        # Ignore private variables
        if var.startswith("_"):
            continue

        fields[var] = getattr(cls, var)

    return fields


TClass = TypeVar("TClass")


def class_inheritors(cls: Type[TClass]) -> List[Type[TClass]]:
    subclasses = set()
    work = [cls]

    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)

    return list(subclasses)
