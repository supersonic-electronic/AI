"""
PDF text extraction module using PyMuPDF.

This module provides a PDFIngestor class for extracting text and metadata
from PDF files and saving them as separate text and JSON files.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

import fitz  # PyMuPDF


class PDFIngestor:
    """
    A class for ingesting PDF files and extracting text and metadata.
    
    This class processes PDF files from an input directory, extracts their text
    content and metadata, and saves the results to separate output directories.
    """
    
    def __init__(self, input_dir: Path, text_dir: Path, meta_dir: Path) -> None:
        """
        Initialize the PDFIngestor with input and output directories.
        
        Args:
            input_dir: Directory containing PDF files to process
            text_dir: Directory where extracted text files will be saved
            meta_dir: Directory where metadata JSON files will be saved
        """
        self.input_dir = Path(input_dir)
        self.text_dir = Path(text_dir)
        self.meta_dir = Path(meta_dir)
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file using PyMuPDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content from all pages
            
        Raises:
            Exception: If PDF cannot be opened or processed
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            empty_pages = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text with reading order preserved
                page_text = page.get_text(sort=True)
                
                if not page_text.strip():
                    empty_pages.append(page_num + 1)
                    self.logger.warning(f"Empty page found: {page_num + 1} in {pdf_path.name}")
                
                text_content.append(page_text)
            
            doc.close()
            
            if empty_pages:
                self.logger.info(f"Document {pdf_path.name} has {len(empty_pages)} empty pages: {empty_pages}")
            
            return "\n".join(text_content)
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
            
        Raises:
            Exception: If PDF cannot be opened or metadata cannot be extracted
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            doc.close()
            
            # Clean and structure metadata
            clean_metadata = {
                'filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'title': metadata.get('title', '').strip(),
                'author': metadata.get('author', '').strip(),
                'subject': metadata.get('subject', '').strip(),
                'creator': metadata.get('creator', '').strip(),
                'producer': metadata.get('producer', '').strip(),
                'creation_date': metadata.get('creationDate', '').strip(),
                'modification_date': metadata.get('modDate', '').strip(),
                'keywords': metadata.get('keywords', '').strip(),
            }
            
            # Look for DOI in metadata or title
            doi = ''
            for field in ['title', 'subject', 'keywords']:
                field_value = clean_metadata.get(field, '')
                if 'doi:' in field_value.lower():
                    # Extract DOI
                    doi_start = field_value.lower().find('doi:')
                    doi = field_value[doi_start:].split()[0]
                    break
            
            clean_metadata['doi'] = doi
            
            # Remove empty values
            clean_metadata = {k: v for k, v in clean_metadata.items() if v}
            
            return clean_metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            raise
    
    def save_text(self, text: str, pdf_path: Path) -> Path:
        """
        Save extracted text to a file.
        
        Args:
            text: Text content to save
            pdf_path: Original PDF file path (used to generate output filename)
            
        Returns:
            Path to the saved text file
        """
        output_path = self.text_dir / f"{pdf_path.stem}.txt"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.logger.info(f"Text saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving text for {pdf_path.name}: {e}")
            raise
    
    def save_metadata(self, meta: Dict[str, Any], pdf_path: Path) -> Path:
        """
        Save metadata to a JSON file.
        
        Args:
            meta: Metadata dictionary to save
            pdf_path: Original PDF file path (used to generate output filename)
            
        Returns:
            Path to the saved JSON file
        """
        output_path = self.meta_dir / f"{pdf_path.stem}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Metadata saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving metadata for {pdf_path.name}: {e}")
            raise
    
    def process_all(self) -> None:
        """
        Process all PDF files in the input directory.
        
        Iterates through all .pdf files in the input directory and processes
        each one by extracting text and metadata, then saving the results.
        Logs successes and failures for each file.
        """
        pdf_files = list(self.input_dir.glob("*.pdf"))
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.input_dir}")
            return
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        success_count = 0
        failure_count = 0
        
        for pdf_path in pdf_files:
            try:
                self.logger.info(f"Processing: {pdf_path.name}")
                
                # Extract text and metadata
                text = self.extract_text(pdf_path)
                metadata = self.extract_metadata(pdf_path)
                
                # Save results
                self.save_text(text, pdf_path)
                self.save_metadata(metadata, pdf_path)
                
                success_count += 1
                self.logger.info(f"Successfully processed: {pdf_path.name}")
                
            except Exception as e:
                failure_count += 1
                self.logger.error(f"Failed to process {pdf_path.name}: {e}")
        
        self.logger.info(f"Processing complete. Successes: {success_count}, Failures: {failure_count}")


def main() -> None:
    """
    Command-line interface for PDFIngestor.
    """
    parser = argparse.ArgumentParser(
        description="Extract text and metadata from PDF files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing PDF files to process"
    )
    
    parser.add_argument(
        "--text-dir",
        type=Path,
        required=True,
        help="Directory where extracted text files will be saved"
    )
    
    parser.add_argument(
        "--meta-dir",
        type=Path,
        required=True,
        help="Directory where metadata JSON files will be saved"
    )
    
    args = parser.parse_args()
    
    # Create and run the ingestor
    ingestor = PDFIngestor(args.input_dir, args.text_dir, args.meta_dir)
    ingestor.process_all()


if __name__ == "__main__":
    main()