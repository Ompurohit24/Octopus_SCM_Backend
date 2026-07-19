import re
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader


class ImportPDFService:
    @staticmethod
    def _clean(value: str | None) -> str:
        if not value:
            return ""

        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _date_to_iso(value: str | None) -> str:
        if not value:
            return ""

        value = value.strip()

        formats = (
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
        )

        for fmt in formats:
            try:
                return datetime.strptime(
                    value,
                    fmt,
                ).date().isoformat()
            except ValueError:
                continue

        return ""

    def extract_text(self, content: bytes) -> str:
        reader = PdfReader(BytesIO(content))

        pages: list[str] = []

        for page in reader.pages:
            text = page.extract_text() or ""

            if text:
                pages.append(text)

        return "\n".join(pages)

    def extract_import_job(
        self,
        content: bytes,
    ) -> dict:
        text = self.extract_text(content)

        if not text.strip():
            raise ValueError(
                "No readable text found in PDF. "
                "The PDF may be scanned and require OCR."
            )

        data: dict[str, object] = {}

        # ---------------------------------------------------------
        # BL NO + BL DATE
        # ---------------------------------------------------------

        # First try the combined checklist format:
        #
        # B/L No. & Date
        # ONEYIZMG03997500
        # 06-Jun-2026

        bl_combined_match = re.search(
            r"B/?L\s*No\.?\s*&\s*Date"
            r".{0,300}?"
            r"\b([A-Z]{3,}[A-Z0-9\-\/]*\d[A-Z0-9\-\/]*)\b"
            r"\s+"
            r"(\d{1,2}[-/.][A-Za-z]{3,9}[-/.]\d{4}|"
            r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if bl_combined_match:
            data["blNo"] = self._clean(
                bl_combined_match.group(1)
            )

            data["blDate"] = self._date_to_iso(
                bl_combined_match.group(2)
            )

        else:
            # Fallback BL number
            bl_match = re.search(
                r"(?:MASTER\s*)?B/?L\s*"
                r"(?:NO\.?|NUMBER)"
                r"\s*[:\-]?\s*"
                r"([A-Z0-9\-\/]+)",
                text,
                re.IGNORECASE,
            )

            if bl_match:
                bl_no = self._clean(
                    bl_match.group(1)
                )

                # Avoid matching heading words.
                if bl_no.upper() not in {
                    "VALUE",
                    "DATE",
                    "NO",
                    "NUMBER",
                }:
                    data["blNo"] = bl_no

            # Fallback BL date
            bl_date_match = re.search(
                r"B/?L\s*DATE"
                r"\s*[:\-]?\s*"
                r"(\d{1,2}[-/.][A-Za-z]{3,9}[-/.]\d{4}|"
                r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
                text,
                re.IGNORECASE,
            )

            if bl_date_match:
                data["blDate"] = self._date_to_iso(
                    bl_date_match.group(1)
                )

        # ---------------------------------------------------------
        # INVOICE NO + INVOICE DATE
        # ---------------------------------------------------------

        # Checklist format:
        #
        # Invoice No. & Date
        # 2026-1414
        # 06-Jun-2026

        invoice_combined_match = re.search(
            r"Invoice\s*No\.?\s*&\s*Date"
            r".{0,300}?"
            r"\b([A-Z0-9]+(?:[-/][A-Z0-9]+)+)\b"
            r"\s+"
            r"(\d{1,2}[-/.][A-Za-z]{3,9}[-/.]\d{4}|"
            r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if invoice_combined_match:
            data["invoiceNo"] = self._clean(
                invoice_combined_match.group(1)
            )

            data["invoiceDate"] = self._date_to_iso(
                invoice_combined_match.group(2)
            )

        else:
            # Fallback invoice number
            invoice_match = re.search(
                r"INVOICE\s*"
                r"(?:NO\.?|NUMBER)"
                r"\s*[:\-]?\s*"
                r"([A-Z0-9]+(?:[-/][A-Z0-9]+)+)",
                text,
                re.IGNORECASE,
            )

            if invoice_match:
                invoice_no = self._clean(
                    invoice_match.group(1)
                )

                if invoice_no.upper() not in {
                    "VALUE",
                    "DATE",
                    "NO",
                    "NUMBER",
                }:
                    data["invoiceNo"] = invoice_no

            # Fallback invoice date
            invoice_date_match = re.search(
                r"INVOICE\s*DATE"
                r"\s*[:\-]?\s*"
                r"(\d{1,2}[-/.][A-Za-z]{3,9}[-/.]\d{4}|"
                r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
                text,
                re.IGNORECASE,
            )

            if invoice_date_match:
                data["invoiceDate"] = self._date_to_iso(
                    invoice_date_match.group(1)
                )

        # ---------------------------------------------------------
        # CONSIGNEE / IMPORTER
        # ---------------------------------------------------------

        # Checklist format:
        #
        # Importer Name & Address
        # VOESTALPINE VAE VKN INDIA PRIVATE LIMITED
        # Plot No....

        consignee_match = re.search(
            r"Importer\s*Name\s*&\s*Address"
            r"\s*[:\-]?\s*"
            r"([^\n\r]+)",
            text,
            re.IGNORECASE,
        )

        if consignee_match:
            consignee = self._clean(
                consignee_match.group(1)
            )

            if consignee.upper() not in {
                "VALUE",
                "DETAILS",
                "PARTICULARS",
                "IMPORTER NAME & ADDRESS",
            }:
                data["consigneeName"] = consignee

        # Generic fallback
        if not data.get("consigneeName"):
            consignee_patterns = (
                r"IMPORTER\s*NAME\s*[:\-]?\s*([^\n\r]+)",
                r"CONSIGNEE\s*(?:NAME)?"
                r"\s*[:\-]?\s*([^\n\r]+)",
            )

            for pattern in consignee_patterns:
                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE,
                )

                if not match:
                    continue

                value = self._clean(
                    match.group(1)
                )

                if (
                    value
                    and value.upper()
                    not in {
                        "VALUE",
                        "DETAILS",
                        "PARTICULARS",
                    }
                ):
                    data["consigneeName"] = value
                    break

        # ---------------------------------------------------------
        # PORT OF LOADING
        # ---------------------------------------------------------

        pol_match = re.search(
            r"(?:PORT\s*OF\s*LOADING|LOAD\s*PORT)"
            r"\s*[:\-]?\s*"
            r"([^\n\r]+)",
            text,
            re.IGNORECASE,
        )

        if pol_match:
            value = self._clean(
                pol_match.group(1)
            )

            if value.upper() not in {
                "VALUE",
                "DETAILS",
            }:
                data["portOfLoading"] = value

        # ---------------------------------------------------------
        # COUNTRY OF ORIGIN
        # ---------------------------------------------------------

        country_match = re.search(
            r"(?:COUNTRY\s*OF\s*ORIGIN|ORIGIN\s*COUNTRY)"
            r"\s*[:\-]?\s*"
            r"([^\n\r]+)",
            text,
            re.IGNORECASE,
        )

        if country_match:
            value = self._clean(
                country_match.group(1)
            )

            if value.upper() not in {
                "VALUE",
                "DETAILS",
            }:
                data["country"] = value

        # ---------------------------------------------------------
        # CONTAINERS
        # ---------------------------------------------------------

        # ISO container number:
        # 4 letters + 7 digits
        #
        # Example:
        # DFSU1259598 20 FCL

        container_matches = re.findall(
            r"\b([A-Z]{4}\d{7})\b"
            r".{0,40}?"
            r"\b(20|40)\b"
            r"(?:\s*(?:FT|HC|FCL|GP))?",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        containers: list[dict[str, str]] = []
        seen: set[str] = set()

        for number, size in container_matches:
            number = number.upper()

            if number in seen:
                continue

            seen.add(number)

            containers.append(
                {
                    "containerNo": number,
                    "size": size,
                }
            )

        if containers:
            data["containers"] = containers
            data["noOfCntr"] = len(containers)

            sizes = {
                container["size"]
                for container in containers
            }

            if len(sizes) == 1:
                data["size"] = next(
                    iter(sizes)
                )

        # ---------------------------------------------------------
        # CARGO DESCRIPTION
        # ---------------------------------------------------------

        cargo_patterns = (
            r"DESCRIPTION\s*OF\s*GOODS"
            r"\s*[:\-]?\s*([^\n\r]+)",

            r"CARGO\s*DESCRIPTION"
            r"\s*[:\-]?\s*([^\n\r]+)",
        )

        for pattern in cargo_patterns:
            cargo_match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not cargo_match:
                continue

            value = self._clean(
                cargo_match.group(1)
            )

            if (
                value
                and value.upper()
                not in {
                    "VALUE",
                    "DETAILS",
                    "PARTICULARS",
                }
            ):
                data["cargoDescription"] = value
                break

        return data


import_pdf_service = ImportPDFService()