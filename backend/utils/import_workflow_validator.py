# class ImportWorkflowValidator:
#
#     @staticmethod
#     def validate(data: dict):
#
#         print("========== VALIDATOR ==========")
#         print(data.get("igm_status"))
#         print(data.get("igm_date"))
#
#         # IGM
#         if data.get("igm_status") == "Done":
#             if not data.get("igm_date"):
#                 raise ValueError("IGM Date is required.")
#
#
#         # if data.get("inward_date"):
#         #
#         #     if data.get("igm_status") != "Done":
#         #         raise ValueError(
#         #             "Complete IGM Status first."
#         #         )
#
#         # BE validation
#
#         if data.get("be_no") and not data.get("inward_date"):
#             raise ValueError("Inward Date is required.")
#
#         # Only validate BE Date when both fields are being used.
#         if data.get("be_no") and not data.get("be_date"):
#             raise ValueError("BE Date is required.")
#
#         if data.get("other_gov_agency") == "Yes":
#
#             if not data.get("other_gov_agency_type"):
#                 raise ValueError(
#                     "Select Type of Other Gov Agency."
#                 )
#
#         if data.get("assessment_type") == "APR":
#
#             if not data.get("cfs_name"):
#                 raise ValueError(
#                     "Select CFS Name."
#                 )
#
#         if data.get("co_deface_required") == "Yes":
#
#             if data.get("co_deface") != "Done":
#                 raise ValueError(
#                     "Complete CO Deface."
#                 )
#
#         if data.get("do_received") == "Done":
#
#             if not data.get("do_validity"):
#                 raise ValueError(
#                     "DO Validity is required."
#                 )
#
#             if not data.get("do_type"):
#                 raise ValueError(
#                     "DO Type is required."
#                 )
#
#         if data.get("transportation") == "Octopus":
#
#             if not data.get("transporter"):
#                 raise ValueError(
#                     "Select Transporter."
#                 )
#
#         return True


class ImportWorkflowValidator:

    @staticmethod
    def validate(data: dict):

        print("========== VALIDATOR ==========")
        print(data)

        # ---------------- IGM ----------------

        if data.get("igm_status") == "Done":
            if not data.get("igm_date"):
                raise ValueError("IGM Date is required.")

        # ---------------- BE ----------------

        if data.get("be_no"):
            if not data.get("inward_date"):
                raise ValueError("Inward Date is required.")

            if not data.get("be_date"):
                raise ValueError("BE Date is required.")

        # ---------------- Other Govt Agency ----------------

        # ---------------- Other Govt Agency ----------------

        # ---------------- Other Govt Agency ----------------

        if data.get("other_gov_agency") == "Yes":
            services = data.get("other_gov_agency_type") or {}

            if not isinstance(services, dict) or not services:
                raise ValueError("Select Type of Other Gov Agency.")

            for service_name, service in services.items():

                status = service.get("status")

                if not status:
                    raise ValueError(
                        f"{service_name}: Status is required."
                    )

                if status == "Done":

                    unit = (service.get("unit") or "").strip()

                    # Tariff Unit required first
                    if not unit:
                        raise ValueError(
                            f"{service_name}: Tariff Unit is required."
                        )

                    if unit not in ("Container", "BL"):
                        raise ValueError(
                            f"{service_name}: Tariff Unit must be Container or BL."
                        )

                    # BL -> single Tariff Amount required
                    if unit == "BL":

                        tariff = service.get("tariff")

                        if tariff in (None, ""):
                            raise ValueError(
                                f"{service_name}: Tariff Amount is required."
                            )

                    # Container -> 20 and/or 40
                    elif unit == "Container":

                        enable20 = service.get("enable20", False)
                        enable40 = service.get("enable40", False)

                        tariff20 = service.get("tariff20")
                        tariff40 = service.get("tariff40")

                        # At least one container size must be selected
                        if not enable20 and not enable40:
                            raise ValueError(
                                f"{service_name}: Select Container Size 20 or 40."
                            )

                        # 20 selected -> 20 amount required
                        if enable20 and tariff20 in (None, ""):
                            raise ValueError(
                                f"{service_name}: 20 Tariff Amount is required."
                            )

                        # 40 selected -> 40 amount required
                        if enable40 and tariff40 in (None, ""):
                            raise ValueError(
                                f"{service_name}: 40 Tariff Amount is required."
                            )
        # ---------------- Other Govt Agency ----------------
        # existing code...

        # ---------------- Other Services ----------------
        # ---------------- Other Services ----------------

        services = data.get("other_services") or {}

        for service_name, service in services.items():

            status = service.get("status")

            if not status:
                raise ValueError(
                    f"{service_name}: Status is required."
                )

            if status == "Done":

                unit = (service.get("unit") or "").strip()

                if not unit:
                    raise ValueError(
                        f"{service_name}: Tariff Unit is required."
                    )

                if unit not in ("Container", "BL"):
                    raise ValueError(
                        f"{service_name}: Tariff Unit must be Container or BL."
                    )

                # Container validation
                if unit == "Container":

                    enable20 = service.get("enable20", False)
                    enable40 = service.get("enable40", False)

                    if not enable20 and not enable40:
                        raise ValueError(
                            f"{service_name}: Select at least one Container Size."
                        )

                    if enable20 and service.get("tariff20") in (None, ""):
                        raise ValueError(
                            f"{service_name}: 20 Tariff Amount is required."
                        )

                    if enable40 and service.get("tariff40") in (None, ""):
                        raise ValueError(
                            f"{service_name}: 40 Tariff Amount is required."
                        )

                # BL validation
                elif unit == "BL":

                    if service.get("tariff") in (None, ""):
                        raise ValueError(
                            f"{service_name}: Tariff Amount is required."
                        )

        # ---------------- Assessment ----------------

        if data.get("assessment_type") == "APR":
            if not data.get("cfs_name"):
                raise ValueError("Select CFS Name.")

        # ---------------- CO Deface ----------------

        if data.get("co_deface_required") == "Yes":
            if data.get("co_deface") != "Done":
                raise ValueError("Complete CO Deface.")

        # ---------------- DO ----------------

        if data.get("do_received") == "Done":
            if not data.get("do_validity"):
                raise ValueError("DO Validity is required.")

            if not data.get("do_type"):
                raise ValueError("DO Type is required.")

        # ---------------- Transportation ----------------

        if data.get("transportation") == "Octopus":
            if not data.get("transporter"):
                raise ValueError("Select Transporter.")

        return True

