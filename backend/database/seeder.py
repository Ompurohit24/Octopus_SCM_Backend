from backend.repositories.cfs_repository import cfs_repository
from backend.repositories.transporter_repository import transporter_repository
from backend.repositories.other_gov_agency_type_repository import (
    other_gov_agency_type_repository,
)


def seed_masters():

    cfs = [
        "Hind Terminal",
        "Ashutosh",
        "Hind Terminal2",
        "Landmark",
        "Seabird",
        "Ameya",
        "Allcargo",
        "Speedy",
        "Mundhra",
        "Saurashtra",
        "Transworld1",
        "Transworld2",
    ]

    transporters = [
        "Bansal",
        "Sai Logistics",
        "Chamunda",
    ]

    agency_types = [
        "FSSAI",
        "PPQ",
        "CDRUG",
        "Other",
    ]

    for item in cfs:
        if not cfs_repository.find_by_name(item):
            cfs_repository.create(
                {
                    "name": item,
                    "is_active": True,
                    "is_deleted": False,
                }
            )

    for item in transporters:
        if not transporter_repository.find_by_name(item):
            transporter_repository.create(
                {
                    "name": item,
                    "is_active": True,
                    "is_deleted": False,
                }
            )

    for item in agency_types:
        if not other_gov_agency_type_repository.find_by_name(item):
            other_gov_agency_type_repository.create(
                {
                    "name": item,
                    "is_active": True,
                    "is_deleted": False,
                }
            )