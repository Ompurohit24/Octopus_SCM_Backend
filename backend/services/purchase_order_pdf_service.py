from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PurchaseOrderPDFService:

    @staticmethod
    def _value(value):
        if value is None:
            return "-"

        value = str(value).strip()

        return value if value else "-"

    @staticmethod
    def generate(
        purchase_order: dict,
    ) -> bytes:

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "PurchaseOrderTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=18,
            leading=22,
            spaceAfter=12,
        )

        section_style = ParagraphStyle(
            "PurchaseOrderSection",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=6,
        )

        normal_style = styles["BodyText"]

        story = []

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        story.append(
            Paragraph(
                "PURCHASE ORDER",
                title_style,
            )
        )

        po_number = PurchaseOrderPDFService._value(
            purchase_order.get(
                "po_number"
            )
        )

        story.append(
            Paragraph(
                f"<b>PO No:</b> {po_number}",
                normal_style,
            )
        )

        story.append(
            Spacer(
                1,
                8,
            )
        )

        # -------------------------------------------------
        # JOB DETAILS
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Job Details",
                section_style,
            )
        )

        job_data = [
            [
                "Job No",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "job_number"
                    )
                ),
                "BL No",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "bl_no"
                    )
                ),
            ],
            [
                "BE No",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "be_no"
                    )
                ),
                "CFS Name",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "cfs_name"
                    )
                ),
            ],
            [
                "Consignee",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "consignee_name"
                    )
                ),
                "",
                "",
            ],
        ]

        job_table = Table(
            job_data,
            colWidths=[
                30 * mm,
                60 * mm,
                30 * mm,
                60 * mm,
            ],
        )

        job_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (2, 0),
                        (2, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(job_table)

        # -------------------------------------------------
        # SERVICE DETAILS
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Service Details",
                section_style,
            )
        )

        tariff = purchase_order.get(
            "tariff"
        )

        if tariff is not None:
            try:
                tariff_display = (
                    f"{float(tariff):,.2f}"
                )
            except (
                TypeError,
                ValueError,
            ):
                tariff_display = str(tariff)
        else:
            tariff_display = "-"

        service_data = [
            [
                "Category",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "category"
                    )
                ),
            ],
            [
                "Service",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "service_name"
                    )
                ),
            ],
            [
                "Tariff Unit",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "unit"
                    )
                ),
            ],
            [
                "Tariff Amount",
                tariff_display,
            ],
        ]

        service_table = Table(
            service_data,
            colWidths=[
                45 * mm,
                135 * mm,
            ],
        )

        service_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(service_table)

        # -------------------------------------------------
        # SELECTED CONTAINERS
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Selected Containers",
                section_style,
            )
        )

        containers = (
            purchase_order.get(
                "containers",
                [],
            )
            or []
        )

        container_data = [
            [
                "Sr No",
                "Container Number",
                "Size",
            ]
        ]

        for index, container in enumerate(
            containers,
            start=1,
        ):
            container_data.append(
                [
                    str(index),
                    PurchaseOrderPDFService._value(
                        container.get(
                            "container_number"
                        )
                    ),
                    PurchaseOrderPDFService._value(
                        container.get(
                            "size"
                        )
                    ),
                ]
            )

        if not containers:
            container_data.append(
                [
                    "",
                    "No containers selected",
                    "",
                ]
            )

        container_table = Table(
            container_data,
            colWidths=[
                20 * mm,
                120 * mm,
                40 * mm,
            ],
            repeatRows=1,
        )

        container_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (0, -1),
                        "CENTER",
                    ),
                    (
                        "ALIGN",
                        (2, 0),
                        (2, -1),
                        "CENTER",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(container_table)

        # -------------------------------------------------
        # VENDOR DETAILS
        # -------------------------------------------------

        story.append(
            Paragraph(
                "Vendor Details",
                section_style,
            )
        )

        vendor_data = [
            [
                "Vendor Code",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "vendor_code"
                    )
                ),
            ],
            [
                "Vendor Name",
                PurchaseOrderPDFService._value(
                    purchase_order.get(
                        "vendor_name"
                    )
                ),
            ],
        ]

        vendor_table = Table(
            vendor_data,
            colWidths=[
                45 * mm,
                135 * mm,
            ],
        )

        vendor_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(vendor_table)

        story.append(
            Spacer(
                1,
                20,
            )
        )

        story.append(
            Paragraph(
                "This is a system-generated Purchase Order.",
                normal_style,
            )
        )

        document.build(story)

        pdf_bytes = buffer.getvalue()

        buffer.close()

        return pdf_bytes


purchase_order_pdf_service = (
    PurchaseOrderPDFService()
)