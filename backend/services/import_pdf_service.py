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
            page_text = page.extract_text() or ""

            if page_text:
                pages.append(page_text)

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
        #
        # Actual PDF text:
        # BL No. ONEYIZMG03997500 dt. 06-Jun-2026
        # ---------------------------------------------------------

        bl_match = re.search(
            r"\bBL\s*No\.?\s*"
            r"([A-Z0-9/-]+)"
            r"\s+(?:dt\.?|Date)\s*"
            r"(\d{1,2}-[A-Za-z]{3,9}-\d{4})",
            text,
            re.IGNORECASE,
        )

        if bl_match:
            data["blNo"] = self._clean(
                bl_match.group(1)
            )

            data["blDate"] = self._date_to_iso(
                bl_match.group(2)
            )

        else:
            # Page 3 fallback:
            #
            # BL No. ONEYIZMG03997500
            # Date 06-Jun-2026

            shipment_bl_match = re.search(
                r"\bBL\s*No\.?\s*"
                r"([A-Z0-9/-]+)"
                r".{0,150}?"
                r"\bDate\s+"
                r"(\d{1,2}-[A-Za-z]{3,9}-\d{4})",
                text,
                re.IGNORECASE | re.DOTALL,
            )

            if shipment_bl_match:
                data["blNo"] = self._clean(
                    shipment_bl_match.group(1)
                )

                data["blDate"] = self._date_to_iso(
                    shipment_bl_match.group(2)
                )

        # ---------------------------------------------------------
        # INVOICE NO + INVOICE DATE
        #
        # Actual PDF text:
        #
        # Invoice 1 / 1
        # 2026-1414 dt. 06-Jun-2026
        # ---------------------------------------------------------

        invoice_match = re.search(
            r"Invoice\s+\d+\s*/\s*\d+"
            r"\s+"
            r"([A-Z0-9/-]+)"
            r"\s+dt\.?\s*"
            r"(\d{1,2}-[A-Za-z]{3,9}-\d{4})",
            text,
            re.IGNORECASE,
        )

        if invoice_match:
            data["invoiceNo"] = self._clean(
                invoice_match.group(1)
            )

            data["invoiceDate"] = self._date_to_iso(
                invoice_match.group(2)
            )

        # ---------------------------------------------------------
        # CONSIGNEE / IMPORTER
        #
        # Actual PDF text:
        #
        # Importer Detail 0597039747
        # M/S. VOESTALPINE VAE VKN INDIA PRIVATE LIMITED
        # ---------------------------------------------------------

        consignee_match = re.search(
            r"Importer\s+Detail[^\r\n]*"
            r"[\r\n]+"
            r"(?:M/S\.?\s*)?"
            r"([^\r\n]+)",
            text,
            re.IGNORECASE,
        )

        if consignee_match:
            consignee = self._clean(
                consignee_match.group(1)
            )

            if consignee:
                data["consigneeName"] = consignee

        # ---------------------------------------------------------
        # PORT OF LOADING
        #
        # Actual:
        # Port Of Loading Aliaga(TRALI)
        # ---------------------------------------------------------

        port_match = re.search(
            r"Port\s+Of\s+Loading\s+"
            r"([^\r\n]+)",
            text,
            re.IGNORECASE,
        )

        if port_match:
            data["portOfLoading"] = self._clean(
                port_match.group(1)
            )

        # ---------------------------------------------------------
        # COUNTRY OF ORIGIN
        #
        # Actual:
        # Cntry Of Origin TURKEY
        # ---------------------------------------------------------

        country_match = re.search(
            r"Cntry\s+Of\s+Origin\s+"
            r"([^\r\n]+)",
            text,
            re.IGNORECASE,
        )

        if country_match:
            data["countryOfOrigin"] = self._clean(
                country_match.group(1)
            )

        # ---------------------------------------------------------
        # CONTAINERS
        #
        # Actual:
        #
        # 1 DFSU1259598 TRAF28738 20' FCL
        # 2 TCLU3417974 TRAF28740 20' FCL
        # ---------------------------------------------------------

        container_matches = re.findall(
            r"^\s*\d+\s+"
            r"([A-Z]{4}\d{7})"
            r"\s+\S+\s+"
            r"(20|40)'?\s*FCL",
            text,
            re.IGNORECASE | re.MULTILINE,
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

            data["noOfCntr"] = len(
                containers
            )

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
        #
        # Actual item line:
        # 1 25171090 OLIVINE SAND AFS 40-45
        # ---------------------------------------------------------

        cargo_match = re.search(
            r"^\s*\d+\s+"
            r"\d{8}\s+"
            r"([^\r\n]+)",
            text,
            re.MULTILINE,
        )

        if cargo_match:
            cargo = self._clean(
                cargo_match.group(1)
            )

            if cargo:
                data["cargoDescription"] = cargo

        return data


import_pdf_service = ImportPDFService()