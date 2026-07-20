from backend.database.mongo import db


purchase_orders = db["purchase_orders"]


class PurchaseOrderRepository:

    @staticmethod
    def create(data: dict, session=None):
        result = purchase_orders.insert_one(
            data,
            session=session,
        )

        return purchase_orders.find_one(
            {"_id": result.inserted_id},
            session=session,
        )

    @staticmethod
    def get_by_id(po_id):
        return purchase_orders.find_one(
            {"_id": po_id}
        )

    @staticmethod
    def get_by_po_number(po_number: str):
        return purchase_orders.find_one(
            {"po_number": po_number}
        )

    @staticmethod
    def get_by_service(
        job_id: str,
        category: str,
        service_name: str,
    ):
        return purchase_orders.find_one(
            {
                "job_id": job_id,
                "category": category,
                "service_name": service_name,
                "status": {
                    "$ne": "Cancelled"
                },
            }
        )

    @staticmethod
    def list_all(
        search: str = "",
        skip: int = 0,
        limit: int = 100,
    ):
        query = {}

        if search:
            query = {
                "$or": [
                    {
                        "po_number": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "job_number": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "consignee_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "vendor_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                    {
                        "service_name": {
                            "$regex": search,
                            "$options": "i",
                        }
                    },
                ]
            }

        total = purchase_orders.count_documents(query)

        items = list(
            purchase_orders
            .find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    @staticmethod
    def update(po_id, data: dict):
        purchase_orders.update_one(
            {"_id": po_id},
            {
                "$set": data
            },
        )

        return purchase_orders.find_one(
            {"_id": po_id}
        )


purchase_order_repository = PurchaseOrderRepository()