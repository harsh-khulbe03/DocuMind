from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


def build_converter() -> DocumentConverter:
    pipeline_options = PdfPipelineOptions(
        do_ocr=False,
        do_table_structure=True,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


# Single converter instance — heavy to initialise, reuse across calls.
_converter: DocumentConverter | None = None


def get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        _converter = build_converter()
    return _converter


def parse_pdf(pdf_path: Path) -> list[dict]:
    """
    Parse a PDF and return a list of page dicts:
        {"page": int, "text": str}

    Pages with no extractable text are omitted.
    """
    converter = get_converter()
    result = converter.convert(pdf_path)
    doc = result.document

    pages: dict[int, list[str]] = {}

    for item in doc.texts:
        # Skip page headers, footers, and captions — they add noise
        if item.label in ("page_header", "page_footer", "caption"):
            continue

        text = item.text.strip()
        if not text:
            continue

        # item.prov is a list; take the first provenance entry for the page number
        if not item.prov:
            continue

        page_no = item.prov[0].page_no
        pages.setdefault(page_no, []).append(text)

    return [
        {"page": page_no, "text": "\n".join(blocks)}
        for page_no, blocks in sorted(pages.items())
        if blocks
    ]
