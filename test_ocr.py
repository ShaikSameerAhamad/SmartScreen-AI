import pdfplumber
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\91944\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

pdf_path = "C:\AIResumeAnalyzer\software-engineer (1).pdf"  # Update this path

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"\n--- Page {i+1} ---")
        
        # Try text extraction
        text = page.extract_text()
        if text and text.strip():
            print("Extracted via Text Layer:\n", text)
        else:
            # Fallback to OCR
            print("No text layer found. Using OCR...")
            image = page.to_image(resolution=300)
            ocr_text = pytesseract.image_to_string(image.original)
            print("Extracted via OCR:\n", ocr_text)
