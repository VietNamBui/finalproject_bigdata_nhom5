import pdfplumber
import re
import os
import nltk
from nltk.tokenize import word_tokenize
import pandas as pd
import unicodedata
import fitz  # PyMuPDF

# Create output directory
os.makedirs("dataForProject/data/output_clean", exist_ok=True)

# Data directory
data_dir = "dataForProject/data/bigdata/"
all_text = []

def extract_text(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Lỗi trích xuất {pdf_path}: {e}")
        # Fallback to pdfplumber if PyMuPDF fails
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e2:
            print(f"Lỗi trích xuất fallback {pdf_path}: {e2}")
    return text

# Extract all PDFs
for pdf_file in os.listdir(data_dir):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(data_dir, pdf_file)
        text = extract_text(pdf_path)
        text = unicodedata.normalize('NFKC', text)  # Chuẩn hóa Unicode
        all_text.append((pdf_file, text))
        lines = text.split('\n')
        print(f"{pdf_file}: {len(lines)} dòng ban đầu")

# Check total lines
combined_text = "\n".join([text for _, text in all_text])
print(f"Tổng số dòng ban đầu: {len(combined_text.split('\n'))}")

# Save raw text
for pdf_file, text in all_text:
    with open(f"data/output_clean/raw_{pdf_file}.txt", "w", encoding="utf-8") as f:
        f.write(text)

def clean_text(text, source):
    # 1. Remove page numbers
    text = re.sub(r'Page \d+', '', text, flags=re.IGNORECASE)
    
    # 2. Remove headers/footers based on source
    if "TNG_QUAN" in source:
        text = re.sub(r'Trung Tâm Thông tin Khoa học thống kê|Viện KHTK|KS\s*[\w\s]+', '', text, flags=re.IGNORECASE)
    elif "KimAnh" in source:
        text = re.sub(r'ĐH Kinh tế Tài chính|UEF|Kỷ yếu|Hội thảo|Khoa học(?: Công nghệ)?|Thành phố Hồ Chí Minh|Lưu hành nội bộ|Ban biên tập|Lời giới thiệu|TS\s*[\w\s]+|ThS\s*[\w\s]+|KS\s*[\w\s]+|khoa công nghệ thông tin|lần 6|lần thứ 6|tháng 06 năm 2024|vo thi kim anh', '', text, flags=re.IGNORECASE)
    elif "iis_2015" in source:
        text = re.sub(r'Issues in Information Systems|Zakir|Seymour|Berg|jasmine|kristi|tom|minot state university|big data analytics', '', text, flags=re.IGNORECASE)
    elif "sybca" in source:
        text = re.sub(r'Dnyansagar Arts|Commerce College', '', text, flags=re.IGNORECASE)
    elif "48077" in source:
        text = re.sub(r'Viện Thông tin Khoa học xã hội|Nguyễn Lê Phương Hoài', '', text, flags=re.IGNORECASE)
    elif "big-data" in source and "what-is" not in source:
        text = re.sub(r'Adding Value to Manufacturing', '', text, flags=re.IGNORECASE)
    elif "what-is" in source:
        text = re.sub(r'Oracle Corporation', '', text, flags=re.IGNORECASE)
    
    # 3. Remove URLs, DOIs, email domains, and publication metadata
    text = re.sub(r'https?://\S+|www\.\S+|doi\s*[\d/\.\-]+|\b[\w\s\.-]+@\w+\.[\w\.]+|\b[\w\s]+\.(?:com|edu|org)\b|see discussions stats and author profiles for this publication at|all content following this page was', '', text, flags=re.IGNORECASE)
    
    # 4. Remove publication info
    text = re.sub(r'volume\s*\d+\s*issue\s*[\w\s\-()]+?\s*pp\s*\d+\s*-\s*\d+\s*\d{4}|conference\s*paper\s*\w+\s*\d{4}|citations\s*reads|\b\d+\s*\d+\b', '', text, flags=re.IGNORECASE)

    text = re.sub(r'\b(volume|issue|pp|doi|abstract|keywords|citations?|reads?|uploaded by|see (profile|discussions)|author profiles?|conference paper|university|minot state|outlook\.com|@|\.edu|\.org|\.com)\b', '', text, flags=re.IGNORECASE)
    
    # 5. Remove author info and related metadata
    text = re.sub(r'\b\d+\s*publications\b|\bsee\s*profile\b|\buploaded\s*by\s*[\w\s]+|\b\d+\s*citations\b|\babstract\b|\bkeywords\b|\b\d+\s*author\b', '', text, flags=re.IGNORECASE)
    
    # 6. Remove cid characters
    text = re.sub(r'cid[:\s\-]*[\w\d]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(cid)\b', '', text, flags=re.IGNORECASE)  # Loại cả từ đơn lẻ còn sót

    
    # 7. Split into lines before further cleaning
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove special characters
        line = re.sub(r'[^\w\s]', ' ', line)
        # Normalize whitespace
        line = re.sub(r'\s+', ' ', line)
        # Convert to lowercase, remove empty lines
        line = line.strip().lower()
        # Keep lines with sufficient length and no unwanted keywords
        if line and len(line) >= 5 and not any(keyword in line for keyword in ['ban biên tập', 'thư ký', 'lời giới thiệu', 'lưu hành nội bộ', 'trưởng khoa', 'phó trưởng khoa', 'trưởng ngành', 'thư ký khoa', 'abstract', 'keywords', 'volume', 'issue', 'pp', 'khoa học', 'lần 6', 'lần thứ 6', 'trường đại học', 'tháng 06', 'author', 'ton duc thang']):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)



# Clean texts
cleaned_texts = []
for pdf_file, text in all_text:
    cleaned = clean_text(text, pdf_file)
    cleaned_texts.append(cleaned)
    print(f"{pdf_file}: {len(cleaned.split('\n'))} dòng sau làm sạch")

# Combine and save cleaned text
cleaned_combined = "\n".join(cleaned_texts)
lines = cleaned_combined.split('\n')
print(f"Tổng số dòng sau làm sạch: {len(lines)}")

with open("data/output_clean/cleaned_text.txt", "w", encoding="utf-8") as f:
    f.write(cleaned_combined)

# Save individual cleaned texts
for pdf_file, cleaned in zip([f for f in os.listdir(data_dir) if f.endswith(".pdf")], cleaned_texts):
    with open(f"data/output_clean/cleaned_{pdf_file}.txt", "w", encoding="utf-8") as f:
        f.write(cleaned)

# Download NLTK punkt_tab
try:
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    print(f"Lỗi tải punkt_tab: {e}")
    exit(1)


def check_cleaned_text(cleaned_text, filename):
    issues = []
    if 'https' in cleaned_text or 'www' in cleaned_text:
        issues.append("URL still present")
    if 'cid' in cleaned_text.lower():
        issues.append("CID characters still present")
    if any(keyword in cleaned_text.lower() for keyword in ['university', 'conference paper', 'kỷ yếu', '@', 'volume', 'issue', 'pp', 'abstract', 'keywords', 'outlook com', 'minotstateu edu', 'khoa học', 'lần 6', 'lần thứ 6', 'trường đại học', 'tháng 06', 'author']):
        issues.append("Metadata still present")
    if issues:
        print(f"Warning in {filename}: {issues}")

for pdf_file, cleaned in zip([f for f in os.listdir(data_dir) if f.endswith(".pdf")], cleaned_texts):
    check_cleaned_text(cleaned, pdf_file)

# Log removed lines for debugging
def log_removed_lines(text, cleaned_text, source):
    original_lines = text.split('\n')
    cleaned_lines = cleaned_text.split('\n')
    with open("data/output_clean/log.txt", "a", encoding="utf-8") as log:
        log.write(f"\nRemoved lines from {source}:\n")
        for line in original_lines:
            if line.strip() and line.strip().lower() not in [cl.strip().lower() for cl in cleaned_lines]:
                log.write(f"{line}\n")

for pdf_file, text, cleaned in zip([f for f in os.listdir(data_dir) if f.endswith(".pdf")], [t for _, t in all_text], cleaned_texts):
    log_removed_lines(text, cleaned, pdf_file)