import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARS = 100_000
MAX_DOCX_DECOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB


@dataclass(frozen=True)
class TextExtraction:
    text: str
    warnings: list[str]


def _decode_text(file_bytes: bytes, warnings: list[str]) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        warnings.append(
            "Document text was decoded as Latin-1 after UTF-8 decoding failed."
        )
        return file_bytes.decode("latin-1")


def extract_text_from_rtf(rtf_content: str) -> str:
    """
    Extracts readable text from an RTF document string.
    Removes RTF control words, font tables, color tables, and binary groups.
    """
    destinations_to_ignore = {
        "fonttbl", "colortbl", "stylesheet", "info", "pict", "header", "footer",
        "headerl", "headerr", "headerf", "footerl", "footerr", "footerf",
        "xmlnstbl", "object", "generator", "author", "operator", "title",
        "subject", "keywords", "doccomm", "creatim", "revtim", "printim", "buptim",
    }

    tokens = re.findall(
        r"\\\\|\\\{|\\\}|\\\'[0-9a-fA-F]{2}|\\u-?\d+\??|\\\*|\\[a-zA-Z]+-?\d* ?|[{}]|[^{}\\\\]+",
        rtf_content,
    )

    output = []
    ignoring_stack = []

    for token in tokens:
        if token == "{":
            ignoring_stack.append(False)
        elif token == "}":
            if ignoring_stack:
                ignoring_stack.pop()
        elif token == r"\\":
            if not any(ignoring_stack):
                output.append("\\")
        elif token == r"\{":
            if not any(ignoring_stack):
                output.append("{")
        elif token == r"\}":
            if not any(ignoring_stack):
                output.append("}")
        elif token == r"\*":
            if ignoring_stack:
                ignoring_stack[-1] = True
        elif token.startswith("\\u"):
            if not any(ignoring_stack):
                m = re.match(r"\\u(-?\d+)", token)
                if m:
                    codepoint = int(m.group(1))
                    if codepoint < 0:
                        codepoint += 65536
                    try:
                        output.append(chr(codepoint))
                    except Exception:
                        pass
        elif token.startswith(r"\'"):
            if not any(ignoring_stack):
                hex_val = token[2:4]
                try:
                    output.append(bytes.fromhex(hex_val).decode("latin-1"))
                except Exception:
                    pass
        elif token.startswith("\\"):
            m = re.match(r"\\([a-zA-Z]+)", token)
            if m:
                word = m.group(1)
                if word in destinations_to_ignore:
                    if ignoring_stack:
                        ignoring_stack[-1] = True
                elif not any(ignoring_stack):
                    if word in ("par", "line"):
                        output.append("\n")
                    elif word == "tab":
                        output.append("\t")
        else:
            if not any(ignoring_stack):
                output.append(token)

    result = "".join(output)
    lines = [line.strip() for line in result.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    if len(cleaned) > MAX_EXTRACTED_CHARS:
        raise ValueError(
            f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
        )
    return cleaned


def extract_text_with_warnings(file_bytes: bytes, filename: str) -> TextExtraction:
    """
    Extracts plain text from PDF, Word (.docx), RTF, Markdown (.md), or plain text files.
    Enforces resource bounds to prevent parsing denial of service.
    """
    ext = Path(filename).suffix.lower()
    warnings: list[str] = []

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
                else:
                    warnings.append(
                        f"PDF page {len(extracted_pages) + len(warnings) + 1} did not contain extractable text."
                    )
            return TextExtraction(text="\n\n".join(extracted_pages), warnings=warnings)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {str(e)}")

    # 2. Word (.docx, .doc)
    if ext in [".docx", ".doc"]:
        # Guard against decompression bombs in zip-based docx and doc files
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                if total_uncompressed > MAX_DOCX_DECOMPRESSED_BYTES:
                    raise ValueError(
                        f"Document exceeds maximum decompressed size limit of 50 MB (got {total_uncompressed // (1024*1024)} MB)."
                    )
        except zipfile.BadZipFile:
            if ext == ".doc":
                raise ValueError("Legacy .doc binary format is not supported. Please convert and save your resume as .docx or .pdf.")

        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
        except ValueError:
            raise
        except Exception as e:
            if ext == ".doc":
                raise ValueError("Legacy .doc binary format is not supported. Please convert and save your resume as .docx or .pdf.")
            raise ValueError(f"Failed to read Word document: {str(e)}. Please save as .docx or .pdf.")

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
        return TextExtraction(text="\n\n".join(lines), warnings=warnings)

    # 3. RTF
    if ext == ".rtf":
        rtf_raw = _decode_text(file_bytes, warnings)
        return TextExtraction(text=extract_text_from_rtf(rtf_raw), warnings=warnings)

    # 4. Markdown / Plain Text / Other
    text = _decode_text(file_bytes, warnings)

    if len(text) > MAX_EXTRACTED_CHARS:
        raise ValueError(
            f"Extracted document text exceeds maximum limit of {MAX_EXTRACTED_CHARS:,} characters."
        )
    return TextExtraction(text=text, warnings=warnings)


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract text using the legacy string-only parser interface."""
    return extract_text_with_warnings(file_bytes, filename).text
