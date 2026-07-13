from pymongo import ReturnDocument

from backend.database.mongo import db

counters = db["counters"]


class CounterRepository:

    @staticmethod
    def initialize(sequence_name: str, start: int = 0):

        counters.update_one(
            {"_id": sequence_name},
            {
                "$setOnInsert": {
                    "value": start
                }
            },
            upsert=True,
        )

    @staticmethod
    def next(sequence_name: str, session=None):

        result = counters.find_one_and_update(
            {"_id": sequence_name},
            {
                "$inc": {
                    "value": 1
                }
            },
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result["value"]


counter_repository = CounterRepository()