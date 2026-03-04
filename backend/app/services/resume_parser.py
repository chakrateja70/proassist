from io import BytesIO

from docx import Document
from pypdf import PdfReader


SUPPORTED_RESUME_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def extract_resume_text(content: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        return _extract_pdf_text(content)
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx_text(content)
    raise ValueError("Unsupported resume type. Please upload PDF or DOCX.")


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n".join(page for page in pages if page)
    return text.strip()


def _extract_docx_text(content: bytes) -> str:
    doc = Document(BytesIO(content))
    text = "\n".join((paragraph.text or "").strip() for paragraph in doc.paragraphs if paragraph.text)
    return text.strip()
