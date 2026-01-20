import os
from pypdf import PdfReader
from docx import Document

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif ext == '.pdf':
        reader = PdfReader(file_path)
        return "".join([page.extract_text() for page in reader.pages])
    
    elif ext == '.docx':
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    return None

def get_all_resumes(folder_path="resumes"):
    resume_bank = {}
    for filename in os.listdir(folder_path):
        content = extract_text_from_file(os.path.join(folder_path, filename))
        if content:
            resume_bank[filename] = content
    return resume_bank