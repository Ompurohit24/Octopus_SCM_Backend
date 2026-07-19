import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config.settings import settings
from html import escape

class EmailService:

    @staticmethod
    def send_customer_created_email(customer: dict):

        message = MIMEMultipart("alternative")

        message["Subject"] = "Customer Profile Created - Octopus SCM"
        message["From"] = settings.SMTP_FROM
        message["To"] = customer["email"]

        html = f"""
        <html>
            <body style="font-family:Arial,sans-serif;">
                <h2>Welcome to Octopus SCM</h2>

                <p>Dear <b>{customer["customer_name"]}</b>,</p>

                <p>Your customer profile has been successfully created.</p>

                <table cellpadding="6">
                    <tr><td><b>Customer Code</b></td><td>{customer["customer_code"]}</td></tr>
                    <tr><td><b>Name</b></td><td>{customer["customer_name"]}</td></tr>
                    <tr><td><b>Email</b></td><td>{customer["email"]}</td></tr>
                    <tr><td><b>Phone</b></td><td>{customer["phone"]}</td></tr>
                    <tr><td><b>GSTIN</b></td><td>{customer["gstin"]}</td></tr>
                    <tr><td><b>PAN</b></td><td>{customer["pan"]}</td></tr>
                    <tr><td><b>TAN</b></td><td>{customer["tan"]}</td></tr>
                </table>

                <br>

                <p>Thank you for choosing Octopus SCM.</p>

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
    def send_vendor_created_email(vendor: dict):
        message = MIMEMultipart("alternative")

        message["Subject"] = "Vendor Profile Created - Octopus SCM"
        message["From"] = settings.SMTP_FROM
        message["To"] = vendor["email"]

        html = f"""
        <html>
            <body style="font-family:Arial,sans-serif;">

                <h2>Welcome to Octopus SCM</h2>

                <p>Dear <b>{vendor["vendor_name"]}</b>,</p>

                <p>Your vendor profile has been successfully created.</p>

                <table cellpadding="6">
                    <tr><td><b>Vendor Code</b></td><td>{vendor["vendor_code"]}</td></tr>
                    <tr><td><b>Vendor Name</b></td><td>{vendor["vendor_name"]}</td></tr>
                    <tr><td><b>Type of Service</b></td><td>{vendor["type_of_service"]}</td></tr>
                    <tr><td><b>Email</b></td><td>{vendor["email"]}</td></tr>
                    <tr><td><b>Phone</b></td><td>{vendor["phone"]}</td></tr>
                    <tr><td><b>GSTIN</b></td><td>{vendor["gstin"]}</td></tr>
                    <tr><td><b>PAN</b></td><td>{vendor["pan"]}</td></tr>
                </table>

                <br>

                <p>Thank you for being associated with Octopus SCM.</p>

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

email_service = EmailService()
