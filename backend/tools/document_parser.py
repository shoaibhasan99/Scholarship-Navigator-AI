import os
import pymupdf as fitz


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a normal/text-based PDF.
    """

    document = fitz.open(pdf_path)

    full_text = []

    for page_number, page in enumerate(document):
        text = page.get_text("text")

        if text.strip():
            full_text.append(
                f"\n--- PAGE {page_number + 1} ---\n{text}"
            )

    document.close()

    return "\n".join(full_text)


def is_scanned_pdf(pdf_path: str, min_chars_per_page: int = 50) -> bool:
    """
    Determine whether a PDF is likely scanned/image-based.

    If most pages contain very little extractable text,
    treat the document as scanned.
    """

    document = fitz.open(pdf_path)

    pages_with_text = 0

    for page in document:
        text = page.get_text("text").strip()

        if len(text) >= min_chars_per_page:
            pages_with_text += 1

    total_pages = len(document)

    document.close()

    if total_pages == 0:
        return True

    text_ratio = pages_with_text / total_pages

    return text_ratio < 0.5


def render_pdf_to_images(
    pdf_path: str,
    output_folder: str = "temp_pages"
) -> list[str]:
    """
    Convert PDF pages into PNG images.

    These images can later be sent to a multimodal AI model.
    """

    os.makedirs(output_folder, exist_ok=True)

    document = fitz.open(pdf_path)

    image_paths = []

    for page_number, page in enumerate(document):

        # Higher resolution for transcript readability
        matrix = fitz.Matrix(2, 2)

        pix = page.get_pixmap(matrix=matrix)

        filename = os.path.join(
            output_folder,
            f"page_{page_number + 1}.png"
        )

        pix.save(filename)

        image_paths.append(filename)

    document.close()

    return image_paths


def process_document(pdf_path: str) -> dict:
    """
    Main document processing function.

    Detects whether the PDF is text-based or scanned.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"File not found: {pdf_path}"
        )

    scanned = is_scanned_pdf(pdf_path)

    if scanned:

        image_paths = render_pdf_to_images(pdf_path)

        return {
            "document_type": "scanned",
            "text": None,
            "images": image_paths
        }

    else:

        text = extract_text_from_pdf(pdf_path)

        return {
            "document_type": "text",
            "text": text,
            "images": []
        }


# Test manually
if __name__ == "__main__":

    file_path = input("Enter PDF path: ")

    result = process_document(file_path)

    print("\nDocument Type:")
    print(result["document_type"])

    if result["document_type"] == "text":

        print("\nExtracted Text:\n")
        print(result["text"][:3000])

    else:

        print("\nScanned PDF detected.")

        print("\nGenerated Images:")

        for image in result["images"]:
            print(image)