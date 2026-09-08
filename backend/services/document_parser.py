import io
import zipfile
from pathlib import Path
from typing import Optional

MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARS = 100_000
MAX_DOCX_DECOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extracts plain text from PDF, Word (.docx), Markdown, or plain text files.
    Enforces resource bounds to prevent parsing denial of service.
    """
    ext = Path(filename).suffix.lower()

    # 1. PDF
    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise ValueError(f"PDF exceeds maximum allowed page count of {MAX_PDF_PAGES} pages.")
            extracted_pages = []
            total_chars = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    total_chars += len(text)
                    if total_chars > MAX_EXTRACTED_CHARS:
                        raise ValueError(
                            f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
                        )
                    extracted_pages.append(text.strip())
            return "\n\n".join(extracted_pages)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {str(e)}")

    # 2. Word (.docx)
    if ext in [".docx", ".doc"]:
        # Guard against decompression bombs in zip-based docx files
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > MAX_DOCX_DECOMPRESSED_BYTES:
                    raise ValueError(
                        f"Document exceeds maximum decompressed size limit of 50 MB (got {total_uncompressed // (1024*1024)} MB)."
                    )
        except zipfile.BadZipFile:
            pass

        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            lines = []
            total_chars = 0
            for para in doc.paragraphs:
                if para.text.strip():
                    total_chars += len(para.text)
                    if total_chars > MAX_EXTRACTED_CHARS:
                        raise ValueError(
                            f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
                        )
                    lines.append(para.text.strip())
            # Also extract text from any tables in the resume
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        total_chars += len(row_text)
                        if total_chars > MAX_EXTRACTED_CHARS:
                            raise ValueError(
                                f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
                            )
                        lines.append(row_text)
            return "\n\n".join(lines)
        except ValueError:
            raise
        except Exception as e:
            # If docx fails (e.g. legacy binary .doc format), try reading strings as fallback
            try:
                decoded = file_bytes.decode("latin-1", errors="ignore")
                printable = "".join(c if 31 < ord(c) < 127 or c in "\n\r\t" else " " for c in decoded)
                cleaned = "\n".join(line.strip() for line in printable.splitlines() if len(line.strip()) > 3)
                if len(cleaned) > 50:
                    if len(cleaned) > MAX_EXTRACTED_CHARS:
                        raise ValueError(
                            f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
                        )
                    return cleaned
            except ValueError:
                raise
            except Exception:
                pass
            raise ValueError(f"Failed to read Word document: {str(e)}. Please save as .docx or .pdf.")

    # 3. Plain Text / Markdown / Other
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception:
            text = file_bytes.decode("utf-8", errors="ignore")

    if len(text) > MAX_EXTRACTED_CHARS:
        raise ValueError(
            f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
        )
    return text
