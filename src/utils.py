import fitz
import re
import tiktoken
import pprint
import pytesseract
import pymupdf
from PIL import Image
import definitions

pytesseract.pytesseract.tesseract_cmd = definitions.TESSERACT_CMD_PATH


def count_tokens(text: str) -> int:
    """
    Counts the number of tokens in a string using a tokenizer
    that is a close match for Llama 3 models.
    """
    if not isinstance(text, str):
        return 0

    # The 'cl100k_base' encoding is used by GPT-4 and is a good general-purpose
    # tokenizer that gives a very close approximation for Llama 3 models.
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except Exception:
        # Fallback to the rule-of-thumb if tiktoken fails for any reason
        return len(text.split()) * 4 // 3


def pretty_print_dict_of_dict(dictionary):
    for key, value in dictionary.items():
        print(f"{key}")

        for k, v in value.items():
            print(f"    {k}: {v} \n")

        print("\n")


def pretty_print_dict(dictionary):
        for k, v in dictionary.items():
            if k != 'raw_text':
                print(f"        {k}: {v}")

        print("\n")


def extract_text_from_all_pages(paper):
    """
    Extracts text from all pages of a PDF file.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        str: The concatenated text from all pages.
    """
    all_text = ""
    try:
        # Iterate through each page of the document
        for page in paper:
            # Extract text from the current page
            text = page.get_text()
            all_text += text
            # Optional: Add a page separator for clarity

            all_text += "\n--- Page Break ---\n"

        pattern = re.compile(r'\bReferences\b')
        all_text = re.split(pattern, all_text)[0]

        # pattern = re.compile(r'\bCRediT authorship contribution statement\b')
        # all_text = re.split(pattern, all_text)[0]
        #
        # pattern = re.compile(r'\bAppendix\b')
        # all_text = re.split(pattern, all_text)[0]
        #
        # pattern = re.compile(r'\bAuthor contributions\b')
        # all_text = re.split(pattern, all_text)[0]

        # pattern = re.compile(r'\bAcknowledgements\b')
        # all_text = re.split(pattern, all_text)[0]

        # pattern = re.compile(r'CRediT authorship contribution statement', re.IGNORECASE)
        # all_text = re.split(pattern, all_text)[0]

        return all_text

    except Exception as e:
        return f"An error occurred: {e}"


def ocr_page_text(page: pymupdf.Page) -> str:
    """
    Performs OCR on a given page to extract text.
    This robust version converts the page to a Pillow Image object
    to ensure compatibility with Tesseract.

    Args:
        page: A pymupdf Page object.

    Returns:
        The extracted text as a string.
    """
    try:
        # 1. Render the page to a high-resolution image (pixmap)
        pix = page.get_pixmap(dpi=300)

        # --- NEW ROBUST LOGIC ---
        # 2. Determine the image mode (e.g., RGB, Grayscale) from the pixmap
        if pix.n >= 4:  # RGBA or similar
            mode = "RGBA"
        elif pix.n == 3:  # RGB
            mode = "RGB"
        elif pix.n == 1:  # Grayscale
            mode = "L"
        else:
            raise ValueError(f"Unsupported number of components in pixmap: {pix.n}")

        # 3. Create a Pillow Image object from the raw pixmap samples
        img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

        # 4. Use pytesseract to perform OCR on the Pillow Image object
        # This is the most reliable way to interface with Tesseract.
        text = pytesseract.image_to_string(img)
        # --- END OF NEW LOGIC ---

        return text
    except Exception as e:
        print(f"--- OCR Error: {e} ---")
        return ""