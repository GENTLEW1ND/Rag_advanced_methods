from bs4 import BeautifulSoup
import logfire


def parse_html(file_path: str):
    
    """
    Pareses HTML content using Beautiful Soup.
    cleans scripts, styles and extracts readable text for RAG
    """
    
    with logfire.span("HTML Parsing", filename = file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.perser')
            
            # 1. Remove junk (Script, styles, metadata)
            for script in soup[Tag](["script", "style", "meta", "noscript"]):
                script.decompose()
                
            # 2. Extract Text
            text = soup.get_text(separator="\n")
            
            # 3. Clean whitespace (Collaps multiple newlines)
            lines = (line.strip() for line in text.splitlines())
            
            chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
            
            text_clean = '\n'.join(chunk for chunk in chunks if chunk)
            
            
            return text_clean
        
        except Exception as e:
            logfire.error(f"HTML Parse Failed: {e}")
            raise e