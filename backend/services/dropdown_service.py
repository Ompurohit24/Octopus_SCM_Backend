from backend.repositories.cfs_repository import cfs_repository
from backend.repositories.transporter_repository import (
    transporter_repository,
)
from backend.repositories.other_gov_agency_type_repository import (
    other_gov_agency_type_repository,
)
from backend.utils.serializer import serialize_list


class DropdownService:

    @staticmethod
    def get_import_workflow_dropdowns():

        cfs = serialize_list(
            cfs_repository.search(limit=500)
        )

        transporters = serialize_list(
            transporter_repository.search(limit=500)
        )

        other_gov_agency_types = serialize_list(
            other_gov_agency_type_repository.search(limit=500)
        )

        return {
            "assessment_types": [
                "RMS",
                "APR",
            ],
            "do_types": [
                "Factory",
                "Doc destuff",
            ],
            "do_processes": [
                "Mundra",
                "Gandhidham",
                "Party",
            ],
            "transportations": [
                "Octopus",
                "Party",
                "Pending",
            ],
            "cfs": cfs,
            "transporters": transporters,
            "other_gov_agency_types": other_gov_agency_types,
            "other_services": [
                "Insurance",
                "CE Certificate",
                "Phyto",
                "Fumigation",
                "Lashing Chocking",
                "Palletisation",
            ],
        }

    @staticmethod
    def get_cfs(search=""):
        return serialize_list(
            cfs_repository.search(
                search=search,
                limit=500,
            )
        )

    @staticmethod
    def get_transporters(search=""):
        return serialize_list(
            transporter_repository.search(
                search=search,
                limit=500,
            )
        )

    @staticmethod
    def get_other_gov_agency_types(search=""):
        return serialize_list(
            other_gov_agency_type_repository.search(
                search=search,
                limit=500,
            )
        )


dropdown_service = DropdownService()