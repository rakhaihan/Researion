
from app.services.pdf_service import PDFService


def test_pdf_service_generates_bytes():
    service = PDFService()
    pdf = service.generate_pdf(
        title="Test Report",
        markdown_content="# Test Report\n\n## Summary\n\nThis is a test.",
    )

    assert isinstance(pdf, bytes)
    assert len(pdf) > 100
    assert pdf.startswith(b"%PDF")


def test_pdf_service_filename():
    service = PDFService()
    filename = service.build_filename("NVIDIA Stock Analysis")
    assert filename.endswith(".pdf")
    assert "nvidia" in filename
