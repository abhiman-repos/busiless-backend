# rag/extractors.py

import os
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
import io
import chardet

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def extract_text_from_csv(file_path: str) -> str:
    """Extract text from a CSV file (convert to readable text)."""
    try:
        df = pd.read_csv(file_path)
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'rb') as f:
            raw = f.read()
            result = chardet.detect(raw)
            encoding = result['encoding']
        df = pd.read_csv(file_path, encoding=encoding)
    # Convert to text representation
    return df.to_string(index=False)

def extract_text_from_excel(file_path: str) -> str:
    """Extract text from Excel (.xlsx, .xls) file."""
    # Read all sheets
    excel_file = pd.ExcelFile(file_path)
    text_parts = []
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        text_parts.append(f"Sheet: {sheet_name}\n{df.to_string(index=False)}")
    return "\n\n".join(text_parts)

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a Word (.docx) file."""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a plain text file with encoding detection."""
    with open(file_path, 'rb') as f:
        raw = f.read()
        result = chardet.detect(raw)
        encoding = result['encoding'] or 'utf-8'
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # fallback to utf-8 with errors ignored
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

def extract_text_from_file(file_path: str) -> str:
    """
    Main entry point to extract text from a file.
    Detects type by extension and calls the appropriate function.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.csv':
        return extract_text_from_csv(file_path)
    elif ext in ['.xlsx', '.xls']:
        return extract_text_from_excel(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md', '.rst']:
        return extract_text_from_txt(file_path)
    else:
        # Fallback: try to read as text
        return extract_text_from_txt(file_path)