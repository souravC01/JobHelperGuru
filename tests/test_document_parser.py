import io
import docx
import pypdf
import pytest
from backend.services.document_parser import extract_text_from_file

def test_extract_from_text():
    content = b"Senior Software Engineer\nPython, Docker, SQL"
    text = extract_text_from_file(content, "resume.txt")
    assert "Senior Software Engineer" in text
    assert "Python" in text

def test_extract_from_docx():
    doc = docx.Document()
    doc.add_heading("John Doe - Resume", level=1)
    doc.add_paragraph("Full Stack Developer with 5 years experience in React and Node.js.")
    doc.add_paragraph("Skills: TypeScript, PostgreSQL, Docker.")
    
    bio = io.BytesIO()
    doc.save(bio)
    docx_bytes = bio.getvalue()
    
    text = extract_text_from_file(docx_bytes, "my_resume.docx")
    assert "John Doe" in text
    assert "React" in text
    assert "PostgreSQL" in text

def test_extract_from_pdf():
    # Generate minimal valid PDF in-memory with pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    bio = io.BytesIO()
    writer.write(bio)
    pdf_bytes = bio.getvalue()
    
    text = extract_text_from_file(pdf_bytes, "sample.pdf")
    # Even on blank page, should return string without crashing
    assert isinstance(text, str)


def test_doc_decompression_limit_blocks_renamed_bomb():
    import zipfile
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", b"0" * (51 * 1024 * 1024))
    bio.seek(0)
    bomb_bytes = bio.getvalue()

    with pytest.raises(ValueError, match="50 MB"):
        extract_text_from_file(bomb_bytes, "bomb.doc")


def test_doc_renamed_valid_docx_succeeds():
    doc = docx.Document()
    doc.add_heading("Alice Smith", level=1)
    doc.add_paragraph("Python Developer")
    bio = io.BytesIO()
    doc.save(bio)
    text = extract_text_from_file(bio.getvalue(), "resume.doc")
    assert "Alice Smith" in text


def test_doc_binary_format_rejected():
    with pytest.raises(ValueError, match="Legacy .doc binary format is not supported"):
        extract_text_from_file(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"random binary", "legacy.doc")
