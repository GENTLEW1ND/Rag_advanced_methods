import logfire
from unstructured.partition.auto import partition

def parse_office(file_path: str):
    """
    Parses Office docuemnts (.docx, .pptx) using the Unstructured library.
    Unlike PDFs, there formats are structured and lighweight, so they are processed locally.
    """
    with logfire.span("Office Document Parsing", filename=file_path):
        try:
            
            #Unstructured automatically detects if it's docx or pptx
            elements = partition(filename=file_path)
            full_text = "\n".join([str(el) for el in elements])
            
            if not full_text.strip():
                logfire.warning(f" Unstructured retured empty text for {file_path}")
            else:
                logfire.info(f"Successfully parsed {len(full_text)} characters")
                
            return full_text
        
        except Exception as e:
            logfire.error(f"Office parse failed: {e}")
            raise e