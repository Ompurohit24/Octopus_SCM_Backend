from bson import ObjectId


def serialize(document):
    if document is None:
        return None

    if "_id" in document:
        document["id"] = str(document.pop("_id"))

    return document


def serialize_list(documents):
    return [serialize(doc) for doc in documents]