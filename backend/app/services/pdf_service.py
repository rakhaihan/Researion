from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.utils.validators import sanitize_filename


class PDFService:
    def generate_pdf(self, title: str, markdown_content: str) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
        )

        styles = getSampleStyleSheet()
        story: list = []

        story.append(Paragraph(self._escape_html(title), styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        for block in markdown_content.split("\n\n"):
            block = block.strip()
            if not block:
                continue

            if block.startswith("# "):
                story.append(Paragraph(self._escape_html(block[2:]), styles["Heading1"]))
            elif block.startswith("## "):
                story.append(Paragraph(self._escape_html(block[3:]), styles["Heading2"]))
            elif block.startswith("### "):
                story.append(Paragraph(self._escape_html(block[4:]), styles["Heading3"]))
            elif block.startswith("- "):
                for line in block.split("\n"):
                    if line.startswith("- "):
                        story.append(
                            Paragraph(
                                f"&bull; {self._escape_html(line[2:])}",
                                styles["Normal"],
                            )
                        )
            else:
                story.append(Paragraph(self._escape_html(block), styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        return buffer.getvalue()

    def build_filename(self, topic: str) -> str:
        return f"{sanitize_filename(topic)}.pdf"

    @staticmethod
    def _escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
