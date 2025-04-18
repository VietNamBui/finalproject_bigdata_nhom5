import pdfplumber
import os

def check_text_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text()
            return bool(text.strip()), "Text PDF"
    except:
        return False, "Scan PDF"

data_dir = "data/bigdata/"
for pdf_file in os.listdir(data_dir):
    if pdf_file.endswith(".pdf"):
        is_text, pdf_type = check_text_pdf(os.path.join(data_dir, pdf_file))
        print(f"{pdf_file}: {pdf_type}")