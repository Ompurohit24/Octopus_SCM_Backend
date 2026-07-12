from datetime import datetime

from backend.repositories.import_workflow_history_repository import (
    import_workflow_history_repository,
)
from backend.utils.serializer import serialize_list


class ImportWorkflowHistoryService:

    @staticmethod
    def log_changes(
        workflow: dict,
        updated_data: dict,
        user_id: str,
    ):

        history = []

        for field, new_value in updated_data.items():

            if field in [
                "updated_at",
                "updated_by",
                "current_stage",
            ]:
                continue

            old_value = workflow.get(field)

            if old_value == new_value:
                continue

            document = {
                "workflow_id": str(workflow["_id"]),
                "job_id": workflow["job_id"],
                "job_number": workflow["job_number"],
                "field_name": field,
                "old_value": old_value,
                "new_value": new_value,
                "changed_by": user_id,
                "created_at": datetime.utcnow(),
            }

            import_workflow_history_repository.create(
                document
            )

            history.append(document)

        return history

    @staticmethod
    def get_history(
        workflow_id: str,
    ):

        data = import_workflow_history_repository.get_history(
            workflow_id
        )

        return serialize_list(data)


import_workflow_history_service = ImportWorkflowHistoryService()