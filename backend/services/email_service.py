import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config.settings import settings


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

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
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

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(
                settings.SMTP_USERNAME,
                settings.SMTP_PASSWORD,
            )
            server.send_message(message)


email_service = EmailService()