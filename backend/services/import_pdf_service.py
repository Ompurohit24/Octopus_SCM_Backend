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
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
        )

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date().isoformat()
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

    def extract_import_job(self, content: bytes) -> dict:
        text = self.extract_text(content)

        if not text.strip():
            raise ValueError(
                "No readable text found in PDF. "
                "The PDF may be scanned and require OCR."
            )

        data: dict[str, object] = {}

        # ---------------------------------------------------------
        # BL NO
        # ---------------------------------------------------------

        bl_match = re.search(
            r"(?:MASTER\s*)?B/?L\s*(?:NO\.?|NUMBER)?\s*[:\-]?\s*"
            r"([A-Z0-9\-\/]+)",
            text,
            re.IGNORECASE,
        )

        if bl_match:
            data["blNo"] = self._clean(bl_match.group(1))

        # ---------------------------------------------------------
        # BL DATE
        # ---------------------------------------------------------

        bl_date_match = re.search(
            r"B/?L\s*DATE\s*[:\-]?\s*"
            r"(\d{1,2}[-/.][A-Za-z]{3}[-/.]\d{4}|"
            r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
            text,
            re.IGNORECASE,
        )

        if bl_date_match:
            data["blDate"] = self._date_to_iso(
                bl_date_match.group(1).replace("/", "-")
            )

        # ---------------------------------------------------------
        # INVOICE NO
        # ---------------------------------------------------------

        invoice_match = re.search(
            r"INVOICE\s*(?:NO\.?|NUMBER)?\s*[:\-]?\s*"
            r"([A-Z0-9\-\/]+)",
            text,
            re.IGNORECASE,
        )

        if invoice_match:
            data["invoiceNo"] = self._clean(
                invoice_match.group(1)
            )

        # ---------------------------------------------------------
        # INVOICE DATE
        # ---------------------------------------------------------

        invoice_date_match = re.search(
            r"INVOICE\s*DATE\s*[:\-]?\s*"
            r"(\d{1,2}[-/.][A-Za-z]{3}[-/.]\d{4}|"
            r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
            text,
            re.IGNORECASE,
        )

        if invoice_date_match:
            data["invoiceDate"] = self._date_to_iso(
                invoice_date_match.group(1).replace("/", "-")
            )

        # ---------------------------------------------------------
        # CONSIGNEE / IMPORTER
        # ---------------------------------------------------------

        consignee_patterns = (
            r"IMPORTER\s*NAME\s*[:\-]?\s*(.+)",
            r"CONSIGNEE\s*(?:NAME)?\s*[:\-]?\s*(.+)",
        )

        for pattern in consignee_patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                value = self._clean(match.group(1))

                if value:
                    data["consigneeName"] = value
                    break

        # ---------------------------------------------------------
        # PORT OF LOADING
        # ---------------------------------------------------------

        pol_match = re.search(
            r"(?:PORT\s*OF\s*LOADING|LOAD\s*PORT)"
            r"\s*[:\-]?\s*(.+)",
            text,
            re.IGNORECASE,
        )

        if pol_match:
            data["portOfLoading"] = self._clean(
                pol_match.group(1)
            )

        # ---------------------------------------------------------
        # COUNTRY OF ORIGIN
        # ---------------------------------------------------------

        country_match = re.search(
            r"(?:COUNTRY\s*OF\s*ORIGIN|ORIGIN\s*COUNTRY)"
            r"\s*[:\-]?\s*([A-Z ]+)",
            text,
            re.IGNORECASE,
        )

        if country_match:
            data["country"] = self._clean(
                country_match.group(1)
            )

        # ---------------------------------------------------------
        # CONTAINERS
        #
        # Example:
        # DFSU1259598 20 FCL
        # ---------------------------------------------------------

        container_matches = re.findall(
            r"\b([A-Z]{4}\d{7})\b"
            r".{0,30}?"
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
                data["size"] = next(iter(sizes))

        # ---------------------------------------------------------
        # CARGO DESCRIPTION
        # ---------------------------------------------------------

        cargo_match = re.search(
            r"(?:DESCRIPTION\s*OF\s*GOODS|"
            r"CARGO\s*DESCRIPTION)"
            r"\s*[:\-]?\s*(.+)",
            text,
            re.IGNORECASE,
        )

        if cargo_match:
            data["cargoDescription"] = self._clean(
                cargo_match.group(1)
            )

        return data


import_pdf_service = ImportPDFService()