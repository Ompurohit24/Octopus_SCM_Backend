from datetime import datetime
from fastapi import BackgroundTasks
from pymongo.errors import DuplicateKeyError
from backend.database.mongo import client
from backend.models.customer import CustomerCreate, CustomerUpdate
from backend.repositories.counter_repository import counter_repository
from backend.repositories.customer_repository import customer_repository
from backend.services.email_service import email_service
from backend.utils.serializer import serialize, serialize_list


class CustomerService:

    # @staticmethod
    # def generate_customer_code():
    #     number = counter_repository.next("customer")
    #     return f"CUS-{number:04d}"

    @staticmethod
    def generate_customer_code(session=None):
        number = counter_repository.next(
            "customer",
            session=session,
        )
        return f"CUS-{number:04d}"


    # @staticmethod
    # def create(customer: CustomerCreate, user_id: str):
    #
    #     code = CustomerService.generate_customer_code()
    #
    #     document = customer.model_dump()
    #
    #     document.update(
    #         {
    #             "customer_code": code,
    #             "is_active": True,
    #             "is_deleted": False,
    #             "created_by": user_id,
    #             "updated_by": user_id,
    #             "created_at": datetime.utcnow(),
    #             "updated_at": datetime.utcnow(),
    #         }
    #     )
    #
    #     result = customer_repository.create(document)
    #
    #     document["_id"] = result.inserted_id
    #
    #     try:
    #         email_service.send_customer_created_email(document)
    #     except Exception as e:
    #         print(f"Email sending failed: {e}")
    #
    #     return serialize(document)
    @staticmethod
    def create(
            customer: CustomerCreate,
            user_id: str,
            background_tasks: BackgroundTasks,
    ):
        try:
            with client.start_session() as session:
                with session.start_transaction():
                    code = CustomerService.generate_customer_code(
                        session=session,
                    )

                    document = customer.model_dump()

                    document.update(
                        {
                            "customer_code": code,
                            "is_active": True,
                            "is_deleted": False,
                            "created_by": user_id,
                            "updated_by": user_id,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                        }
                    )

                    result = customer_repository.create(
                        document,
                        session=session,
                    )

                    document["_id"] = result.inserted_id

        except DuplicateKeyError:
            raise ValueError("Customer already exists.")

        except Exception:
            raise

        background_tasks.add_task(
            email_service.send_customer_created_email,
            document,
        )

        return serialize(document)


    @staticmethod
    def get_by_id(customer_id: str):

        customer = customer_repository.find_by_id(customer_id)

        if not customer:
            raise ValueError("Customer not found")

        return serialize(customer)

    @staticmethod
    def update(
        customer_id: str,
        customer: CustomerUpdate,
    ):

        data = customer.model_dump(exclude_unset=True)

        data["updated_at"] = datetime.utcnow()

        customer_repository.update(
            customer_id,
            data,
        )

        updated = customer_repository.find_by_id(customer_id)

        return serialize(updated)

    @staticmethod
    def delete(customer_id: str):

        customer_repository.soft_delete(customer_id)

        return {
            "message": "Customer deleted successfully"
        }