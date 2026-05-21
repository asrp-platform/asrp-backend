from sqlalchemy.orm import InstrumentedAttribute


def get_condition(column, operator: str, value):  # noqa
    if operator == "eq":
        return column == value
    elif operator == "ne":
        return column != value
    elif operator == "gt":
        return column > value
    elif operator == "gte":
        return column >= value
    elif operator == "lt":
        return column < value
    elif operator == "lte":
        return column <= value

    elif operator == "icontains":
        return column.ilike(f"%{value}%")
    elif operator == "startswith":
        return column.ilike(f"{value}%")
    elif operator == "endswith":
        return column.endswith(f"%{value}")
    elif operator == "iendswith":
        return column.iendswith(f"%{value}")
    elif operator == "in":
        if column.type.python_type:
            try:
                value = list(map(lambda val: int(val), value.split(",")))
            except ValueError:
                raise ValueError(f"Invalid integer filter for integer column {column}")
        return column.in_(value)

    else:
        raise ValueError(f"Unsupported operator: {operator}")


def build_conditions(model, filters: dict[str, str]):
    conditions = []

    for key, value in filters.items():
        if "__" in key:
            field_name, operator = key.split("__", 1)
            if "__" in operator:  # case for "related_model__column__operator"
                # retrieve related model name
                related_model_name = field_name
                # retrieve column name for related model and operator
                field_name, operator = operator.split("__", 1)
                related_model_attribute = getattr(model, related_model_name)

                target_model = related_model_attribute.property.mapper.class_
                target_column: InstrumentedAttribute = getattr(target_model, field_name, None)
                conditions.append(get_condition(target_column, operator, value))
                continue
        else:
            field_name, operator = key, "eq"

        column: InstrumentedAttribute = getattr(model, field_name)
        if column is None:
            continue

        conditions.append(get_condition(column, operator, value))

    return conditions
