class ImportWorkflowValidator:

    @staticmethod
    def validate(data: dict):

        print("========== VALIDATOR ==========")
        print(data.get("igm_status"))
        print(data.get("igm_date"))

        # IGM
        if data.get("igm_status") == "Done":
            if not data.get("igm_date"):
                raise ValueError("IGM Date is required.")


        # if data.get("inward_date"):
        #
        #     if data.get("igm_status") != "Done":
        #         raise ValueError(
        #             "Complete IGM Status first."
        #         )

        if data.get("be_no"):

            if not data.get("inward_date"):
                raise ValueError(
                    "Inward Date is required."
                )

        if data.get("be_date"):

            if not data.get("be_no"):
                raise ValueError(
                    "BE No is required."
                )

        if data.get("other_gov_agency") == "Yes":

            if not data.get("other_gov_agency_type"):
                raise ValueError(
                    "Select Type of Other Gov Agency."
                )

        if data.get("assessment_type") == "APR":

            if not data.get("cfs_name"):
                raise ValueError(
                    "Select CFS Name."
                )

        if data.get("co_deface_required") == "Yes":

            if data.get("co_deface") != "Done":
                raise ValueError(
                    "Complete CO Deface."
                )

        if data.get("do_received") == "Done":

            if not data.get("do_validity"):
                raise ValueError(
                    "DO Validity is required."
                )

            if not data.get("do_type"):
                raise ValueError(
                    "DO Type is required."
                )

        if data.get("transportation") == "Octopus":

            if not data.get("transporter"):
                raise ValueError(
                    "Select Transporter."
                )

        return True