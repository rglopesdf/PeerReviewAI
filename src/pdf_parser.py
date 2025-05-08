# src/pdf_parser.py

import pypdf
import os

class PDFParser:
    def __init__(self):
        pass

    def extract_text(self, pdf_path):
        """Extracts text from a given PDF file.

        Args:
            pdf_path (str): The absolute path to the PDF file.

        Returns:
            str: The extracted text content from the PDF. Returns an empty string if extraction fails or file not found.
        """
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found at {pdf_path}")
            return ""
        
        try:
            reader = pypdf.PdfReader(pdf_path)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
                if page_num < len(reader.pages) - 1:
                    text += "\n\n--- Page Break ---\n\n" # Add a separator for clarity between pages
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            # In a more robust system, might try OCR or browser rendering here as per knowledge.
            # For now, returning empty string on failure.
            return ""

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    # Create a dummy PDF for testing if one doesn't exist
    # This part would typically be run in an environment where a PDF is available.
    # For now, we'll just show how to call it.
    
    # Create a dummy pdfs directory and a dummy file for testing structure
    if not os.path.exists("/home/ubuntu/academic_evaluator/pdfs"): os.makedirs("/home/ubuntu/academic_evaluator/pdfs")
    # A real PDF would be needed here for actual testing.
    # dummy_pdf_path = "/home/ubuntu/academic_evaluator/pdfs/sample.pdf" 
    # with open(dummy_pdf_path, "w") as f: f.write("This is a dummy PDF content placeholder.") # This is not a real PDF

    parser = PDFParser()
    
    # print(f"Please place a sample PDF at {dummy_pdf_path} for testing.")
    # extracted_content = parser.extract_text(dummy_pdf_path)
    # if extracted_content:
    #     print(f"Extracted content from {dummy_pdf_path}:\n{extracted_content[:500]}...")
    # else:
    #     print(f"Could not extract content from {dummy_pdf_path}.")
    print("PDFParser class defined. To test, place a PDF in academic_evaluator/pdfs/ and call extract_text.")

