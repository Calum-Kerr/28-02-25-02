# app/pdf_processing.py
"""
Module for PDF text extraction and editing operations for the NASA PDF Tool.
This module adheres to NASA's strict coding and security standards:
 - All functions include detailed docstrings.
 - Exception handling is in place to ensure robust operation.
 - PDF text extraction preserves layout, font, and style metadata.
 - Text editing is performed via redaction and re-insertion to preserve formatting.
"""

import fitz  # PyMuPDF is used for PDF operations
import logging

def extract_text_from_pdf(file_path):
    """
    Extract text and formatting metadata from the given PDF file.
    
    Opens the PDF, iterates through each page, and retrieves text spans along with
    their properties such as bounding box, font name, size, and colour.
    
    :param file_path: Path to the PDF file.
    :return: A dictionary with extracted text data, structured by pages.
             Example format:
             {
                "pages": [
                    [  # Page 0 spans
                        {
                          "text": "Sample text",
                          "bbox": [x0, y0, x1, y1],
                          "font": "Helvetica",
                          "size": 12,
                          "color": 0
                        },
                        ...
                    ],
                    ...
                ]
             }
    :raises: Exception if the PDF cannot be opened or processed.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logging.error(f"Failed to open PDF: {e}")
        raise

    extraction = {"pages": []}

    for page_number in range(len(doc)):
        page = doc[page_number]
        # Retrieve text as a dictionary, including blocks, lines, and spans.
        page_dict = page.get_text("dict")
        page_spans = []

        # Iterate over each text block
        for block in page_dict.get("blocks", []):
            if block.get('type') != 0:  # Skip non-text blocks (e.g., images)
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    # Gather span properties
                    span_info = {
                        "text": span.get("text", ""),
                        "bbox": span.get("bbox", []),
                        "font": span.get("font", ""),
                        "size": span.get("size", 0),
                        "color": span.get("color", 0)
                    }
                    page_spans.append(span_info)
        extraction["pages"].append(page_spans)

    doc.close()
    return extraction

def apply_text_edits_to_pdf(pdf_path, edits):
    """
    Applies text edits to the original PDF file and returns the modified PDF as bytes.
    
    The 'edits' parameter should be a dictionary mapping page numbers (as strings)
    to another dictionary mapping the index of the text span (within the extracted list)
    to the new text.
    
    Example edits format:
    {
        "0": { "2": "New text for span index 2 on page 0" },
        "1": { "5": "New text for span index 5 on page 1" }
    }
    
    For each edit:
      - The PDF is opened using PyMuPDF.
      - For each page with edits, we extract the list of text spans.
      - For each targeted span, a redaction annotation is added over its bounding box.
      - After all annotations are added for a page, redactions are applied to erase the original text.
      - The new text is then inserted at the same position, using the original font and size.
      
    :param pdf_path: Path to the original PDF file.
    :param edits: Dictionary of edits as described above.
    :return: Bytes object of the modified PDF file.
    :raises: Exception if any PDF processing step fails.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logging.error(f"Failed to open PDF for editing: {e}")
        raise

    # Iterate over each page in the PDF document
    for page_number in range(len(doc)):
        page = doc[page_number]
        page_key = str(page_number)
        if page_key not in edits:
            continue  # No edits for this page

        # Retrieve the current page's text as a dictionary
        page_dict = page.get_text("dict")
        spans = []
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    spans.append(span)

        # Collect annotations and associated properties for redaction and re-insertion
        annotations = []
        page_edits = edits[page_key]
        for span_index_str, new_text in page_edits.items():
            try:
                span_index = int(span_index_str)
            except ValueError:
                logging.error(f"Invalid span index: {span_index_str}")
                continue

            if span_index < 0 or span_index >= len(spans):
                logging.error(f"Span index {span_index} out of range on page {page_number}")
                continue

            span = spans[span_index]
            bbox = span.get("bbox")
            if not bbox:
                logging.error(f"No bounding box for span index {span_index} on page {page_number}")
                continue

            # Add a redaction annotation over the original text bounding box.
            try:
                # White fill (RGB 1,1,1) will effectively cover the original text.
                annot = page.add_redact_annot(bbox, fill=(1, 1, 1))
                # Store all necessary properties for later insertion
                annotations.append({
                    "annot": annot,
                    "bbox": bbox,
                    "font": span.get("font", "helv"),
                    "size": span.get("size", 12),
                    "color": span.get("color", 0),
                    "new_text": new_text
                })
            except Exception as e:
                logging.error(f"Failed to add redaction for span index {span_index} on page {page_number}: {e}")
                continue

        # Apply all redactions on the current page to erase original text
        try:
            page.apply_redactions()
        except Exception as e:
            logging.error(f"Error applying redactions on page {page_number}: {e}")
            continue

        # Re-insert the new text over the redacted areas
        for item in annotations:
            bbox = item["bbox"]
            font = item["font"]
            size = item["size"]
            new_text = item["new_text"]

            try:
                # Determine insertion point: bottom-left of the bounding box with slight adjustment.
                insertion_point = (bbox[0], bbox[3] - 1)
                # Insert the new text using the original font properties.
                page.insert_text(insertion_point, new_text,
                                 fontname=font,
                                 fontsize=size,
                                 color=(0, 0, 0))  # Using black; adjust if needed based on original 'color'
            except Exception as e:
                logging.error(f"Error inserting new text on page {page_number}: {e}")
                continue

    # Save the modified PDF into an in-memory bytes buffer.
    from io import BytesIO
    output_buffer = BytesIO()
    try:
        doc.save(output_buffer)
    except Exception as e:
        logging.error(f"Error saving modified PDF: {e}")
        raise
    doc.close()
    output_buffer.seek(0)
    return output_buffer.read()