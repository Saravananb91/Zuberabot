import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from zuberabot.utils.pdf import extract_text_from_pdf
from zuberabot.ai.ingestion import IngestionService
from zuberabot.database.postgres import init_database, get_db_manager

def ingest_all_pdfs(directory: str):
    logger.info(f"Starting ingestion from {directory}")
    init_database()  # Ensure database is initialized
    
    ingestion_service = IngestionService()
    
    # "Zuberabot user" is the user_id for generic b2c context
    system_user_id = "system:zuberabot"
    
    # Ensure system user exists
    db = get_db_manager()
    db.get_or_create_user("zuberabot", channel="system", name="System")
    
    
    for filename in os.listdir(directory):
        if filename.lower().endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            logger.info(f"Processing {filename}...")
            
            text = extract_text_from_pdf(filepath)
            
            if text.startswith("Error:"):
                logger.error(text)
                continue
                
            if not text.strip():
                logger.warning(f"No text extracted from {filename}")
                continue
                
            metadata = {
                "source": "b2c_user_stories",
                "filename": filename,
                "context": "general"
            }
            
            # Determine category from filename
            category = "general"
            lower_name = filename.lower()
            if "mutual fund" in lower_name:
                category = "mutual_funds"
            elif "net worth" in lower_name:
                category = "finance"
            elif "profile" in lower_name:
                category = "profile"
            elif "onboarding" in lower_name or "kyc" in lower_name:
                category = "onboarding"
                
            metadata["category"] = category
            
            doc = ingestion_service.ingest_document(
                user_id=system_user_id,
                content=text,
                filename=filename,
                metadata=metadata
            )
            
            logger.info(f"Successfully ingested {filename} with doc ID {doc.id}")
            
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    b2c_dir = r"E:\demo projects\zuberaa\zuberabot\b2c user stories"
    
    # Check if a PDF library is installed
    try:
        import fitz
    except ImportError:
        try:
            import PyPDF2
        except ImportError:
            logger.error("Please run: pip install pymupdf")
            sys.exit(1)
            
    if not os.path.exists(b2c_dir):
        logger.error(f"Directory not found: {b2c_dir}")
        sys.exit(1)
        
    ingest_all_pdfs(b2c_dir)
