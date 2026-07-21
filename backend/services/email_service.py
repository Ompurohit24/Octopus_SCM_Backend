import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from backend.config.settings import settings
from html import escape

class EmailService:

    @staticmethod
    def send_customer_created_email(customer: dict):

        # -------------------------------------------------
        # NORMALIZE RECIPIENT EMAILS
        #
        # Backward compatible:
        # email: "abc@example.com"
        #
        # New:
        # email: [
        #     "abc@example.com",
        #     "accounts@example.com",
        # ]
        # -------------------------------------------------

        raw_emails = customer.get("email", [])

        if isinstance(raw_emails, str):
            emails = [raw_emails]
        elif isinstance(raw_emails, list):
            emails = raw_emails
        else:
            emails = []

        # Clean + remove duplicates case-insensitively.
        recipients = []
        seen = set()

        for item in emails:
            email = str(item).strip()

            if not email:
                continue

            normalized = email.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            recipients.append(email)

        # Do not attempt SMTP if no valid recipient exists.
        if not recipients:
            return

        # -------------------------------------------------
        # EMAIL MESSAGE
        # -------------------------------------------------

        message = MIMEMultipart("alternative")

        message["Subject"] = (
            "Customer Profile Created - Octopus SCM"
        )

        message["From"] = settings.SMTP_FROM

        # Visible recipients.
        message["To"] = ", ".join(recipients)




        email_display = ", ".join(recipients)

        html = f"""
        <html>
            <body style="font-family:Arial,sans-serif;">

                <h2>Welcome to Octopus SCM</h2>

                <p>
                    Dear <b>{customer["customer_name"]}</b>,
                </p>

                <p>
                    Your customer profile has been
                    successfully created.
                </p>

                <table cellpadding="6">

                    <tr>
                        <td><b>Customer Code</b></td>
                        <td>{customer["customer_code"]}</td>
                    </tr>

                    <tr>
                        <td><b>Name</b></td>
                        <td>{customer["customer_name"]}</td>
                    </tr>

                    <tr>
                        <td><b>Email</b></td>
                        <td>{email_display}</td>
                    </tr>

                    <tr>
                        <td><b>Phone</b></td>
                        <td>{customer["phone"]}</td>
                    </tr>

                    <tr>
                        <td><b>GSTIN</b></td>
                        <td>{customer["gstin"]}</td>
                    </tr>

                    <tr>
                        <td><b>PAN</b></td>
                        <td>{customer["pan"]}</td>
                    </tr>

                    <tr>
                        <td><b>TAN</b></td>
                        <td>{customer["tan"]}</td>
                    </tr>

                </table>

                <br>

                <p>
                    Thank you for choosing Octopus SCM.
                </p>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        # -------------------------------------------------
        # SMTP
        # -------------------------------------------------

        with smtplib.SMTP(
                settings.SMTP_HOST,
                int(settings.SMTP_PORT),
                timeout=30,
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            # IMPORTANT:
            # Explicitly pass every email as an SMTP recipient.
            server.sendmail(
                settings.SMTP_FROM,
                recipients,
                message.as_string(),
            )
    @staticmethod
    def send_vendor_created_email(vendor: dict):

        # Supports both old and new vendor records:
        #
        # Old:
        # email: "vendor@example.com"
        #
        # New:
        # email: [
        #     "vendor@example.com",
        #     "accounts@example.com",
        # ]

        raw_emails = vendor.get("email", [])

        if isinstance(raw_emails, str):
            emails = [raw_emails]

        elif isinstance(raw_emails, list):
            emails = raw_emails

        else:
            emails = []

        # Clean and remove duplicate emails
        # case-insensitively.
        recipients = []
        seen = set()

        for item in emails:
            email = str(item).strip()

            if not email:
                continue

            normalized = email.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            recipients.append(email)

        # Avoid SMTP call when there is no recipient.
        if not recipients:
            return

        message = MIMEMultipart("alternative")

        message["Subject"] = (
            "Vendor Profile Created - Octopus SCM"
        )

        message["From"] = settings.SMTP_FROM

        # Display all recipients in To.
        message["To"] = ", ".join(recipients)

        email_display = ", ".join(recipients)

        html = f"""
        <html>
            <body style="font-family:Arial,sans-serif;">

                <h2>Welcome to Octopus SCM</h2>

                <p>
                    Dear <b>{vendor["vendor_name"]}</b>,
                </p>

                <p>
                    Your vendor profile has been
                    successfully created.
                </p>

                <table cellpadding="6">

                    <tr>
                        <td><b>Vendor Code</b></td>
                        <td>{vendor["vendor_code"]}</td>
                    </tr>

                    <tr>
                        <td><b>Vendor Name</b></td>
                        <td>{vendor["vendor_name"]}</td>
                    </tr>

                    <tr>
                        <td><b>Type of Service</b></td>
                        <td>{vendor["type_of_service"]}</td>
                    </tr>

                    <tr>
                        <td><b>Email</b></td>
                        <td>{email_display}</td>
                    </tr>

                    <tr>
                        <td><b>Phone</b></td>
                        <td>{vendor["phone"]}</td>
                    </tr>

                    <tr>
                        <td><b>GSTIN</b></td>
                        <td>{vendor["gstin"]}</td>
                    </tr>

                    <tr>
                        <td><b>PAN</b></td>
                        <td>{vendor["pan"]}</td>
                    </tr>

                </table>

                <br>

                <p>
                    Thank you for working with Octopus SCM.
                </p>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        with smtplib.SMTP(
                settings.SMTP_HOST,
                int(settings.SMTP_PORT),
                timeout=30,
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            # Send the same Vendor Created email
            # to every registered vendor email.
            server.sendmail(
                settings.SMTP_FROM,
                recipients,
                message.as_string(),
            )

    @staticmethod
    def send_import_job_created_email(email: str, job: dict):

        message = MIMEMultipart("alternative")

        message["Subject"] = f"Import Job Created - {job['job_number']}"
        message["From"] = settings.SMTP_FROM
        message["To"] = email

        html = f"""
        <html>
            <body style="font-family:Arial,sans-serif;">

                <h2>Import Job Created Successfully</h2>

                <p>Dear <b>{job["forwarder"]}</b>,</p>

                <p>Your import job has been successfully created.</p>

                <table cellpadding="6" cellspacing="0">

                    <tr>
                        <td><b>Job Number</b></td>
                        <td>{job["job_number"]}</td>
                    </tr>

                    <tr>
                        <td><b>BL No</b></td>
                        <td>{job["bl_no"]}</td>
                    </tr>

                    <tr>
                        <td><b>BL Date</b></td>
                        <td>{job["bl_date"]}</td>
                    </tr>

                    <tr>
                        <td><b>Invoice No</b></td>
                        <td>{job["invoice_no"]}</td>
                    </tr>

                    <tr>
                        <td><b>Invoice Date</b></td>
                        <td>{job["invoice_date"]}</td>
                    </tr>

                    <tr>
                        <td><b>No Of Container</b></td>
                        <td>{job["no_of_cntr"]}</td>
                    </tr>

                    <tr>
                        <td><b>Size</b></td>
                        <td>{job["size"]}</td>
                    </tr>

                    <tr>
                        <td><b>Line Name</b></td>
                        <td>{job["line_name"]}</td>
                    </tr>

                    <tr>
                        <td><b>Name of Forwarder</b></td>
                        <td>{job["forwarder"]}</td>
                    </tr>

                    <tr>
                        <td><b>ETA</b></td>
                        <td>{job["eta"]}</td>
                    </tr>

                    <tr>
                        <td><b>Name of Consignee</b></td>
                        <td>{job["consignee_name"]}</td>
                    </tr>

                    <tr>
                        <td><b>Address of Consignee</b></td>
                        <td>{job["consignee_address"]}</td>
                    </tr>

                    <tr>
                        <td><b>Cargo Description</b></td>
                        <td>{job["cargo_description"]}</td>
                    </tr>

                </table>

                <br>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(
                settings.SMTP_HOST,
                int(settings.SMTP_PORT),
                timeout=30,
        ) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            server.send_message(message)
    @staticmethod
    def send_pending_jobs_email(
        pending_sections: list[dict],
    ):
        # ---------------------------------------------------------
        # TEMPORARY TEST RECIPIENTS
        #
        # Later:
        # TO will come dynamically from Import Operations Master.
        # ---------------------------------------------------------

        to_emails = [
            "ompurohit787@gmail.com",
        ]

        cc_emails = [
            "prakashnbhatt3@gmail.com",
        ]

        if not pending_sections:
            return

        message = MIMEMultipart("alternative")

        message["Subject"] = (
            "Octopus SCM - Daily Pending Jobs Report"
        )

        message["From"] = settings.SMTP_FROM

        message["To"] = ", ".join(
            to_emails
        )

        message["Cc"] = ", ".join(
            cc_emails
        )

        sections_html = ""

        for section in pending_sections:

            title = escape(
                str(
                    section.get(
                        "title",
                        "Pending Jobs",
                    )
                )
            )

            jobs = section.get(
                "jobs",
                [],
            )

            if not jobs:
                continue

            rows_html = ""

            for job in jobs:

                job_number = escape(
                    str(
                        job.get(
                            "job_number",
                            "",
                        )
                        or ""
                    )
                )

                bl_no = escape(
                    str(
                        job.get(
                            "bl_no",
                            "",
                        )
                        or ""
                    )
                )

                consignee_name = escape(
                    str(
                        job.get(
                            "consignee_name",
                            "",
                        )
                        or ""
                    )
                )

                eta = escape(
                    str(
                        job.get(
                            "eta",
                            "",
                        )
                        or ""
                    )
                )

                rows_html += f"""
                    <tr>
                        <td style="
                            padding:8px;
                            border:1px solid #ddd;
                        ">
                            {job_number}
                        </td>

                        <td style="
                            padding:8px;
                            border:1px solid #ddd;
                        ">
                            {bl_no}
                        </td>

                        <td style="
                            padding:8px;
                            border:1px solid #ddd;
                        ">
                            {consignee_name}
                        </td>

                        <td style="
                            padding:8px;
                            border:1px solid #ddd;
                        ">
                            {eta}
                        </td>
                    </tr>
                """

            sections_html += f"""
                <h3 style="
                    margin-top:24px;
                    margin-bottom:8px;
                ">
                    {title}
                </h3>

                <table
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        width:100%;
                        max-width:1000px;
                        border-collapse:collapse;
                    "
                >
                    <thead>
                        <tr>
                            <th style="
                                padding:8px;
                                border:1px solid #ddd;
                                text-align:left;
                            ">
                                Job No
                            </th>

                            <th style="
                                padding:8px;
                                border:1px solid #ddd;
                                text-align:left;
                            ">
                                BL No
                            </th>

                            <th style="
                                padding:8px;
                                border:1px solid #ddd;
                                text-align:left;
                            ">
                                Consignee
                            </th>

                            <th style="
                                padding:8px;
                                border:1px solid #ddd;
                                text-align:left;
                            ">
                                ETA
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            """

        # Do not send an empty report.
        if not sections_html:
            return

        html = f"""
        <html>
            <body style="
                font-family:Arial,sans-serif;
                color:#222;
            ">

                <h2>
                    Daily Pending Jobs Report
                </h2>

                <p>
                    Dear Operations Team,
                </p>

                <p>
                    Please find below the Import Jobs
                    requiring pending operational action.
                </p>

                {sections_html}

                <br>

                <p>
                    Please review the above jobs and update
                    the corresponding activities in
                    Octopus SCM.
                </p>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        # Important:
        # CC must be included in SMTP recipients as well as
        # in the visible Cc header.
        recipients = list(
            dict.fromkeys(
                to_emails
                + cc_emails
            )
        )

        with smtplib.SMTP(
            settings.SMTP_HOST,
            int(settings.SMTP_PORT),
            timeout=30,
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            server.sendmail(
                settings.SMTP_FROM,
                recipients,
                message.as_string(),

           )

    @staticmethod
    def send_purchase_order_email(
            vendor: dict,
            purchase_order: dict,
            pdf_bytes: bytes,
    ):
        # -------------------------------------------------
        # NORMALIZE VENDOR EMAILS
        #
        # Supports:
        # email: "vendor@example.com"
        #
        # and:
        # email: [
        #     "vendor@example.com",
        #     "accounts@example.com",
        # ]
        # -------------------------------------------------

        raw_emails = vendor.get("email", [])

        if isinstance(raw_emails, str):
            emails = [raw_emails]

        elif isinstance(raw_emails, list):
            emails = raw_emails

        else:
            emails = []

        recipients = []
        seen = set()

        for item in emails:
            email = str(item).strip()

            if not email:
                continue

            normalized = email.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            recipients.append(email)

        if not recipients:
            return

        # -------------------------------------------------
        # SAFE DISPLAY VALUES
        # -------------------------------------------------

        po_number = escape(
            str(
                purchase_order.get(
                    "po_number",
                    "",
                )
                or ""
            )
        )

        job_number = escape(
            str(
                purchase_order.get(
                    "job_number",
                    "",
                )
                or ""
            )
        )

        bl_no = escape(
            str(
                purchase_order.get(
                    "bl_no",
                    "",
                )
                or ""
            )
        )

        be_no = escape(
            str(
                purchase_order.get(
                    "be_no",
                    "",
                )
                or ""
            )
        )

        cfs_name = escape(
            str(
                purchase_order.get(
                    "cfs_name",
                    "",
                )
                or ""
            )
        )

        consignee_name = escape(
            str(
                purchase_order.get(
                    "consignee_name",
                    "",
                )
                or ""
            )
        )

        service_name = escape(
            str(
                purchase_order.get(
                    "service_name",
                    "",
                )
                or ""
            )
        )

        category = escape(
            str(
                purchase_order.get(
                    "category",
                    "",
                )
                or ""
            )
        )

        unit = escape(
            str(
                purchase_order.get(
                    "unit",
                    "",
                )
                or ""
            )
        )

        tariff = purchase_order.get(
            "tariff"
        )

        tariff_display = (
            f"{float(tariff):,.2f}"
            if tariff is not None
            else "-"
        )

        vendor_name = escape(
            str(
                vendor.get(
                    "vendor_name",
                    purchase_order.get(
                        "vendor_name",
                        "",
                    ),
                )
                or ""
            )
        )

        # -------------------------------------------------
        # CONTAINER HTML
        # -------------------------------------------------

        containers = purchase_order.get(
            "containers",
            [],
        ) or []

        container_rows = ""

        for container in containers:
            container_number = escape(
                str(
                    container.get(
                        "container_number",
                        "",
                    )
                    or ""
                )
            )

            size = escape(
                str(
                    container.get(
                        "size",
                        "",
                    )
                    or ""
                )
            )

            container_rows += f"""
            <tr>
                <td
                    style="
                        padding:6px;
                        border:1px solid #ddd;
                    "
                >
                    {container_number}
                </td>

                <td
                    style="
                        padding:6px;
                        border:1px solid #ddd;
                    "
                >
                    {size}
                </td>
            </tr>
            """

        if not container_rows:
            container_rows = """
            <tr>
                <td
                    colspan="2"
                    style="
                        padding:6px;
                        border:1px solid #ddd;
                    "
                >
                    -
                </td>
            </tr>
            """

        # -------------------------------------------------
        # EMAIL
        # -------------------------------------------------

        message = MIMEMultipart("mixed")

        message["Subject"] = (
            f"Purchase Order {po_number} - "
            f"Octopus SCM"
        )

        message["From"] = settings.SMTP_FROM

        message["To"] = ", ".join(
            recipients
        )

        html = f"""
        <html>
            <body
                style="
                    font-family:Arial,sans-serif;
                    color:#222;
                "
            >

                <h2>Purchase Order Issued</h2>

                <p>
                    Dear <b>{vendor_name}</b>,
                </p>

                <p>
                    Please find attached Purchase Order
                    <b>{po_number}</b>.
                </p>

                <table
                    cellpadding="6"
                    cellspacing="0"
                >
                    <tr>
                        <td><b>PO Number</b></td>
                        <td>{po_number}</td>
                    </tr>

                    <tr>
                        <td><b>Job Number</b></td>
                        <td>{job_number}</td>
                    </tr>

                    <tr>
                        <td><b>BL No</b></td>
                        <td>{bl_no or "-"}</td>
                    </tr>

                    <tr>
                        <td><b>BE No</b></td>
                        <td>{be_no or "-"}</td>
                    </tr>

                    <tr>
                        <td><b>Consignee</b></td>
                        <td>{consignee_name or "-"}</td>
                    </tr>

                    <tr>
                        <td><b>CFS Name</b></td>
                        <td>{cfs_name or "-"}</td>
                    </tr>

                    <tr>
                        <td><b>Category</b></td>
                        <td>{category}</td>
                    </tr>

                    <tr>
                        <td><b>Service</b></td>
                        <td>{service_name}</td>
                    </tr>

                    <tr>
                        <td><b>Tariff Unit</b></td>
                        <td>{unit or "-"}</td>
                    </tr>

                    <tr>
                        <td><b>Tariff Amount</b></td>
                        <td>{tariff_display}</td>
                    </tr>
                </table>

                <h3>Selected Containers</h3>

                <table
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        border-collapse:collapse;
                        width:100%;
                        max-width:600px;
                    "
                >
                    <thead>
                        <tr>
                            <th
                                style="
                                    padding:6px;
                                    border:1px solid #ddd;
                                    text-align:left;
                                "
                            >
                                Container Number
                            </th>

                            <th
                                style="
                                    padding:6px;
                                    border:1px solid #ddd;
                                    text-align:left;
                                "
                            >
                                Size
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        {container_rows}
                    </tbody>
                </table>

                <br>

                <p>
                    The Purchase Order PDF is attached
                    to this email.
                </p>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        # -------------------------------------------------
        # PDF ATTACHMENT
        # -------------------------------------------------

        attachment = MIMEApplication(
            pdf_bytes,
            _subtype="pdf",
        )

        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"{po_number}.pdf",
        )

        message.attach(attachment)

        # -------------------------------------------------
        # SMTP
        # -------------------------------------------------

        with smtplib.SMTP(
                settings.SMTP_HOST,
                int(settings.SMTP_PORT),
                timeout=30,
        ) as server:

            server.ehlo()
            server.starttls()
            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            server.sendmail(
                settings.SMTP_FROM,
                recipients,
                message.as_string(),
            )

    @staticmethod
    def send_purchase_order_cancellation_email(
        vendor: dict,
        purchase_order: dict,
    ):
        # -------------------------------------------------
        # NORMALIZE VENDOR EMAILS
        #
        # Supports:
        #
        # email: "vendor@example.com"
        #
        # and:
        #
        # email: [
        #     "vendor@example.com",
        #     "accounts@example.com",
        # ]
        # -------------------------------------------------

        raw_emails = vendor.get(
            "email",
            [],
        )

        if isinstance(
            raw_emails,
            str,
        ):
            emails = [
                raw_emails
            ]

        elif isinstance(
            raw_emails,
            list,
        ):
            emails = raw_emails

        else:
            emails = []

        recipients = []
        seen = set()

        for item in emails:

            email = str(
                item
            ).strip()

            if not email:
                continue

            normalized = (
                email.lower()
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            recipients.append(
                email
            )

        # Do not attempt SMTP when the vendor
        # has no registered email address.

        if not recipients:
            return

        # -------------------------------------------------
        # SAFE DISPLAY VALUES
        # -------------------------------------------------

        po_number = escape(
            str(
                purchase_order.get(
                    "po_number",
                    "",
                )
                or ""
            )
        )

        job_number = escape(
            str(
                purchase_order.get(
                    "job_number",
                    "",
                )
                or ""
            )
        )

        bl_no = escape(
            str(
                purchase_order.get(
                    "bl_no",
                    "",
                )
                or ""
            )
        )

        be_no = escape(
            str(
                purchase_order.get(
                    "be_no",
                    "",
                )
                or ""
            )
        )

        consignee_name = escape(
            str(
                purchase_order.get(
                    "consignee_name",
                    "",
                )
                or ""
            )
        )

        category = escape(
            str(
                purchase_order.get(
                    "category",
                    "",
                )
                or ""
            )
        )

        service_name = escape(
            str(
                purchase_order.get(
                    "service_name",
                    "",
                )
                or ""
            )
        )

        cancellation_reason = escape(
            str(
                purchase_order.get(
                    "cancellation_reason",
                    "Service removed from Import Workflow",
                )
                or "Service removed from Import Workflow"
            )
        )

        vendor_name = escape(
            str(
                vendor.get(
                    "vendor_name",
                    purchase_order.get(
                        "vendor_name",
                        "",
                    ),
                )
                or ""
            )
        )

        vendor_code = escape(
            str(
                vendor.get(
                    "vendor_code",
                    purchase_order.get(
                        "vendor_code",
                        "",
                    ),
                )
                or ""
            )
        )

        # -------------------------------------------------
        # EMAIL MESSAGE
        # -------------------------------------------------

        message = MIMEMultipart(
            "alternative"
        )

        message["Subject"] = (
            f"Purchase Order Cancelled - "
            f"{po_number} - "
            f"{service_name}"
        )

        message["From"] = (
            settings.SMTP_FROM
        )

        message["To"] = ", ".join(
            recipients
        )

        html = f"""
        <html>
            <body
                style="
                    font-family:Arial,sans-serif;
                    color:#222;
                "
            >

                <h2>
                    Purchase Order Cancellation
                </h2>

                <p>
                    Dear <b>{vendor_name}</b>,
                </p>

                <p>
                    This is to inform you that the service
                    assigned under Purchase Order
                    <b>{po_number}</b> has been
                    <b>cancelled</b>.
                </p>

                <p>
                    Please discontinue any further work
                    related to the service mentioned below.
                </p>

                <table
                    cellpadding="6"
                    cellspacing="0"
                >

                    <tr>
                        <td>
                            <b>PO Number</b>
                        </td>

                        <td>
                            {po_number or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Job Number</b>
                        </td>

                        <td>
                            {job_number or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>BL No</b>
                        </td>

                        <td>
                            {bl_no or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>BE No</b>
                        </td>

                        <td>
                            {be_no or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Consignee</b>
                        </td>

                        <td>
                            {consignee_name or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Category</b>
                        </td>

                        <td>
                            {category or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Service</b>
                        </td>

                        <td>
                            <b>{service_name or "-"}</b>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Vendor Code</b>
                        </td>

                        <td>
                            {vendor_code or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Status</b>
                        </td>

                        <td>
                            <b>Cancelled</b>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Cancellation Reason</b>
                        </td>

                        <td>
                            {cancellation_reason}
                        </td>
                    </tr>

                </table>

                <br>

                <p>
                    Kindly acknowledge this cancellation
                    and treat the previously issued
                    Purchase Order as cancelled.
                </p>

                <p>
                    No further action is required against
                    this Purchase Order unless separately
                    instructed by Octopus SCM.
                </p>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        # -------------------------------------------------
        # SMTP
        # -------------------------------------------------

        with smtplib.SMTP(
            settings.SMTP_HOST,
            int(
                settings.SMTP_PORT
            ),
            timeout=30,
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            # Send cancellation notification to
            # every registered vendor email.

            server.sendmail(
                settings.SMTP_FROM,
                recipients,
                message.as_string(),
            )

    @staticmethod
    def send_purchase_order_invoice_reminder_email(
        vendor: dict,
        purchase_order: dict,
    ) -> bool:
        """
        Send a reminder to the assigned vendor requesting
        submission of the invoice for an Issued PO.

        Returns True only when the SMTP send succeeds.

        This allows the reminder service to update:

            last_invoice_reminder_at
            invoice_reminder_count

        only after successful delivery.
        """

        # -------------------------------------------------
        # NORMALIZE VENDOR EMAILS
        # -------------------------------------------------

        raw_emails = vendor.get(
            "email",
            [],
        )

        if isinstance(
            raw_emails,
            str,
        ):
            emails = [
                raw_emails
            ]

        elif isinstance(
            raw_emails,
            list,
        ):
            emails = raw_emails

        else:
            emails = []

        recipients = []
        seen = set()

        for item in emails:

            email = str(
                item
            ).strip()

            if not email:
                continue

            normalized = (
                email.lower()
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            recipients.append(
                email
            )

        # No email address means no successful reminder.

        if not recipients:
            return False

        # -------------------------------------------------
        # SAFE DISPLAY VALUES
        # -------------------------------------------------

        po_number = escape(
            str(
                purchase_order.get(
                    "po_number",
                    "",
                )
                or ""
            )
        )

        job_number = escape(
            str(
                purchase_order.get(
                    "job_number",
                    "",
                )
                or ""
            )
        )

        bl_no = escape(
            str(
                purchase_order.get(
                    "bl_no",
                    "",
                )
                or ""
            )
        )

        be_no = escape(
            str(
                purchase_order.get(
                    "be_no",
                    "",
                )
                or ""
            )
        )

        consignee_name = escape(
            str(
                purchase_order.get(
                    "consignee_name",
                    "",
                )
                or ""
            )
        )

        category = escape(
            str(
                purchase_order.get(
                    "category",
                    "",
                )
                or ""
            )
        )

        service_name = escape(
            str(
                purchase_order.get(
                    "service_name",
                    "",
                )
                or ""
            )
        )

        vendor_name = escape(
            str(
                vendor.get(
                    "vendor_name",
                    purchase_order.get(
                        "vendor_name",
                        "",
                    ),
                )
                or ""
            )
        )

        vendor_code = escape(
            str(
                vendor.get(
                    "vendor_code",
                    purchase_order.get(
                        "vendor_code",
                        "",
                    ),
                )
                or ""
            )
        )

        # -------------------------------------------------
        # EMAIL
        # -------------------------------------------------

        message = MIMEMultipart(
            "alternative"
        )

        message["Subject"] = (
            f"Invoice Required - "
            f"{po_number} - "
            f"{job_number}"
        )

        message["From"] = (
            settings.SMTP_FROM
        )

        message["To"] = ", ".join(
            recipients
        )

        # -------------------------------------------------
        # FIXED CC RECIPIENTS
        # -------------------------------------------------

        cc_recipients = [
            "prakashnbhatt3@gmail.com",
            "bhattprakassh@gmail.com",
        ]

        message["Cc"] = ", ".join(
            cc_recipients
        )

        html = f"""
        <html>
            <body
                style="
                    font-family:Arial,sans-serif;
                    color:#222;
                "
            >

                <h2>
                    Invoice Submission Reminder
                </h2>

                <p>
                    Dear <b>{vendor_name}</b>,
                </p>

                <p>
                    This is a reminder to submit your invoice
                    against Purchase Order
                    <b>{po_number}</b>.
                </p>

                <p>
                    Our records indicate that the vendor invoice
                    for the following Purchase Order has not yet
                    been received.
                </p>

                <table
                    cellpadding="6"
                    cellspacing="0"
                >

                    <tr>
                        <td>
                            <b>PO Number</b>
                        </td>

                        <td>
                            {po_number or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Job Number</b>
                        </td>

                        <td>
                            {job_number or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>BL No</b>
                        </td>

                        <td>
                            {bl_no or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>BE No</b>
                        </td>

                        <td>
                            {be_no or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Consignee</b>
                        </td>

                        <td>
                            {consignee_name or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Category</b>
                        </td>

                        <td>
                            {category or "-"}
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Service</b>
                        </td>

                        <td>
                            <b>{service_name or "-"}</b>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <b>Vendor Code</b>
                        </td>

                        <td>
                            {vendor_code or "-"}
                        </td>
                    </tr>

                </table>

                <br>

                <p>
                    Kindly send the invoice at the earliest
                    so that it can be recorded and processed
                    in Octopus SCM.
                </p>

                <p>
                    This reminder will automatically stop once
                    the invoice is received and uploaded against
                    this Purchase Order.
                </p>

                <p>
                    Regards,<br>
                    Octopus SCM Team
                </p>

            </body>
        </html>
        """

        message.attach(
            MIMEText(
                html,
                "html",
            )
        )

        # -------------------------------------------------
        # SMTP
        # -------------------------------------------------

        with smtplib.SMTP(
            settings.SMTP_HOST,
            int(
                settings.SMTP_PORT
            ),
            timeout=30,
        ) as server:

            server.ehlo()

            server.starttls()

            server.ehlo()

            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )

            all_recipients = list(
                dict.fromkeys(
                    recipients
                    + cc_recipients
                )
            )

            server.sendmail(
                settings.SMTP_FROM,
                all_recipients,
                message.as_string(),
            )
        return True




email_service = EmailService()
