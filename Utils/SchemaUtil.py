from typing import TypeVar

from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


def rows_to_schema(schema_cls: type[M], rows, extra_names: tuple[str, ...]) -> list[M]:
    items = []
    for row in rows:
        orm_obj = row[0]
        extras = row[1:]
        data = {c.name: getattr(orm_obj, c.name) for c in orm_obj.__table__.columns}
        for name, value in zip(extra_names, extras):
            data[name] = value
        items.append(schema_cls.model_validate(data))
    return items
