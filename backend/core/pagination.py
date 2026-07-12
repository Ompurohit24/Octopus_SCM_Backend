from math import ceil


def paginate(
    total: int,
    page: int,
    size: int,
    items: list,
):
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
            "pages": ceil(total / size) if size else 1,
        },
    }