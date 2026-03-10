import os

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
        
    try:
        from pypdf import PdfReader
        text = ""
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except ImportError:
        return "Error: No PDF library installed. Please install pypdf (pip install pypdf)."
