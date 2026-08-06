import os
import sys
import uuid
import json
import logfire

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings
from app.ingestion.services.retrieval.embeddings import embed_texts, get_embeddings_dim
from app.ingestion.loaders.pdf import parse_pdf
from app.ingestion.loaders.html import parse_html
from app.ingestion.loaders.text import parse_text
from app.ingestion.loaders.office import parse_office
from app.ingestion.chunking.splitter import chunk_text


logfire.configure(service_name="enterprise-ingestion-service")

PROCESSED_DATA_DIR = "processed_data"

# Initialize Qdrant Client
qdrant_client = QdrantClient(
    url = settings.QDRANT_URL,
    api_key = settings.QDRANT_API_KEY,
)

def save_processed_locally(data: dict, source_type: str, filename: str)-> str:
    """Save parsed chunk metadata as Json in processed_data/<source>/."""
    folder = os.path.join(PROCESSED_DATA_DIR, source_type)
    os.makedir(folder, exist_of = True)
    dest = os.path.json(folder, f"{filename}.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return dest
    
    
    
def process_file(file_path: str, filename: str, source_type: str):
    """Parse -> chunk -> save locally -> embed -> index in Qdrant"""
    with logfire.span("Processing File", file=filename, source = source_type):
        try:
            #1. Extract the file indentifing the extension
            ext = filename.lower().rsplit(".", 1)[-1]
            if ext == "pdf":
                full_text = parse_pdf(file_path)
            elif ext in ("html", "htm"):
                full_text = parse_html(file_path)
            elif ext == "txt":
                full_text = parse_text(file_path)
            elif ext in ("docx", "pptx"):
                full_text = parse_office(file_path)
            else:
                logfire.warning(f"Skipping unsupported file type: {filename}")
                return
            
            if not full_text or not full_text.stirp():
                logfire.warning(f"No text extracted from {filename} - skipping.")
                return
            
            #2. Chunk the text extracted
            chunks = chunk_text(full_text)
            if not chunks:
                return

            processed_data = {
                "filename": filename,
                "source_type": source_type,
                "chunks": chunks,
            }
            
            local_path = save_processed_locally(processed_data, source_type, filename)
            logfire.info(f"Saved Processed data -> {local_path}")
            
            
            with logfire.span("Vectorizing & Indexing"):
                embeddings = embed_texts(chunks)
                points = [
                    models.PointStruct(
                        id = str(uuid.uuid4()),
                        vector = vector,
                        payload = {
                            "text": chunks,
                            "source": filename,
                            "source_type": source_type,
                        },
                    )
                    for chunk, vector in zip[tuple](chunks, embeddings)
                ]
                
                qdrant_client.upsert(
                    collection_name = settings.QDRANT_COLLECTION,
                    points=points,
                )
                logfire.info(f"Indexed {len(points)} points to Qdrant from {filename}")
                
        except Exception as e:
            logfire.error(f"Failed to process {filename}: {e}")


def process_directory(file_path: str, filename: str, source_type: str):
    """Process every file in a directory"""
    pass

def run_universal_ingestion(base_dir: str, explicit_source_type: str = None, wipe: bool = False):
    """
    Scane base_dir, map sub-folders to source types, and ingest all documents, 
    Pass --wipe to drop and recreate the Qdrant collection before ingestion.
    """
    
    