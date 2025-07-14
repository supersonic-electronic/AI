"""
PDF text extraction module using PyMuPDF with YAML configuration support.

This module provides a PDFIngestor class for extracting text and metadata
from PDF files and saving them as separate text and JSON files.
"""

import argparse
import json
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Optional

import fitz  # PyMuPDF
import yaml
from tqdm import tqdm


class PDFIngestor:
    """
    A class for ingesting PDF files and extracting text and metadata.
    
    This class processes PDF files from an input directory, extracts their text
    content and metadata, and saves the results to separate output directories.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the PDFIngestor with configuration.
        
        Args:
            config: Configuration dictionary loaded from YAML
        """
        self.config = config
        self.input_dir = Path(config['input_dir'])
        self.text_dir = Path(config['text_dir'])
        self.meta_dir = Path(config['meta_dir'])
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Compile DOI regex pattern
        self.doi_pattern = re.compile(config.get('doi_regex', r'10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*'))
        self.doi_prefixes = config.get('doi_prefixes', ['doi:', 'DOI:', 'https://doi.org/', 'http://dx.doi.org/'])
    
    def _setup_logging(self) -> None:
        """Setup logging configuration based on config settings."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if enabled
        if self.config.get('log_to_file', False):
            log_file = Path(self.config.get('log_file', './logs/pdf_ingestion.log'))
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
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
                # Extract text with reading order preserved if configured
                sort_text = self.config.get('preserve_reading_order', True)
                page_text = page.get_text(sort=sort_text)
                
                if not page_text.strip():
                    empty_pages.append(page_num + 1)
                    if self.config.get('warn_empty_pages', True):
                        self.logger.warning(f"Empty page found: {page_num + 1} in {pdf_path.name}")
                
                text_content.append(page_text)
            
            doc.close()
            
            if empty_pages and self.config.get('warn_empty_pages', True):
                self.logger.info(f"Document {pdf_path.name} has {len(empty_pages)} empty pages: {empty_pages}")
            
            return "\n".join(text_content)
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file with improved DOI detection.
        
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
            
            # Enhanced DOI extraction using regex
            doi = self._extract_doi(clean_metadata)
            clean_metadata['doi'] = doi
            
            # Remove empty values
            clean_metadata = {k: v for k, v in clean_metadata.items() if v}
            
            return clean_metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            raise
    
    def _extract_doi(self, metadata: Dict[str, Any]) -> str:
        """
        Extract DOI using regex patterns from metadata fields.
        
        Args:
            metadata: Metadata dictionary to search
            
        Returns:
            Extracted DOI string or empty string if not found
        """
        # Search in multiple fields
        search_fields = ['title', 'subject', 'keywords', 'author']
        
        for field in search_fields:
            field_value = metadata.get(field, '')
            if not field_value:
                continue
                
            # First try to find DOI with prefixes
            for prefix in self.doi_prefixes:
                if prefix.lower() in field_value.lower():
                    # Extract text after prefix
                    start_idx = field_value.lower().find(prefix.lower()) + len(prefix)
                    remaining_text = field_value[start_idx:].strip()
                    
                    # Apply regex to extract DOI
                    match = self.doi_pattern.search(remaining_text)
                    if match:
                        return match.group(0)
            
            # Also try direct regex search without prefix
            match = self.doi_pattern.search(field_value)
            if match:
                return match.group(0)
        
        return ''
    
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
            encoding = self.config.get('encoding', 'utf-8')
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(text)
            
            self.logger.debug(f"Text saved to: {output_path}")
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
            encoding = self.config.get('encoding', 'utf-8')
            indent = self.config.get('json_indent', 2)
            
            with open(output_path, 'w', encoding=encoding) as f:
                json.dump(meta, f, indent=indent, ensure_ascii=False)
            
            self.logger.debug(f"Metadata saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving metadata for {pdf_path.name}: {e}")
            raise
    
    def _should_skip_file(self, pdf_path: Path) -> bool:
        """
        Check if file should be skipped based on existing outputs.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if file should be skipped, False otherwise
        """
        if not self.config.get('skip_existing', False):
            return False
            
        text_file = self.text_dir / f"{pdf_path.stem}.txt"
        meta_file = self.meta_dir / f"{pdf_path.stem}.json"
        
        return text_file.exists() and meta_file.exists()
    
    def _process_single_pdf(self, pdf_path: Path) -> tuple[bool, str]:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if self._should_skip_file(pdf_path):
                return True, f"Skipped (already processed): {pdf_path.name}"
            
            # Extract text and metadata
            text = self.extract_text(pdf_path)
            metadata = self.extract_metadata(pdf_path)
            
            # Save results
            self.save_text(text, pdf_path)
            self.save_metadata(metadata, pdf_path)
            
            return True, f"Successfully processed: {pdf_path.name}"
            
        except Exception as e:
            return False, f"Failed to process {pdf_path.name}: {e}"
    
    def process_all(self) -> None:
        """
        Process all PDF files in the input directory with optional parallel processing.
        
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
        
        # Determine if we should use parallel processing
        max_workers = self.config.get('parallel_workers', 1)
        use_parallel = max_workers > 1 and len(pdf_files) > 1
        
        # Setup progress bar if enabled
        show_progress = self.config.get('show_progress', True)
        progress_bar = tqdm(total=len(pdf_files), desc="Processing PDFs") if show_progress else None
        
        try:
            if use_parallel:
                self.logger.info(f"Using parallel processing with {max_workers} workers")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_path = {
                        executor.submit(self._process_single_pdf, pdf_path): pdf_path
                        for pdf_path in pdf_files
                    }
                    
                    # Process completed tasks
                    for future in as_completed(future_to_path):
                        success, message = future.result()
                        
                        if success:
                            success_count += 1
                            self.logger.info(message)
                        else:
                            failure_count += 1
                            self.logger.error(message)
                        
                        if progress_bar:
                            progress_bar.update(1)
            else:
                # Sequential processing
                for pdf_path in pdf_files:
                    success, message = self._process_single_pdf(pdf_path)
                    
                    if success:
                        success_count += 1
                        self.logger.info(message)
                    else:
                        failure_count += 1
                        self.logger.error(message)
                    
                    if progress_bar:
                        progress_bar.update(1)
        
        finally:
            if progress_bar:
                progress_bar.close()
        
        self.logger.info(f"Processing complete. Successes: {success_count}, Failures: {failure_count}")


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.yaml file.
    
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config.yaml is not found
        yaml.YAMLError: If config.yaml is invalid
    """
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_interactive_input(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get interactive input from user with config defaults.
    
    Args:
        config: Base configuration dictionary
        
    Returns:
        Updated configuration with user inputs
    """
    updated_config = config.copy()
    
    print("PDF Ingestion Configuration")
    print("=" * 30)
    
    # Input directory
    default_input = config['input_dir']
    input_dir = input(f"Enter input directory [{default_input}]: ").strip()
    if input_dir:
        updated_config['input_dir'] = input_dir
    
    # Text output directory
    default_text = config['text_dir']
    text_dir = input(f"Enter text output directory [{default_text}]: ").strip()
    if text_dir:
        updated_config['text_dir'] = text_dir
    
    # Metadata directory
    default_meta = config['meta_dir']
    meta_dir = input(f"Enter metadata directory [{default_meta}]: ").strip()
    if meta_dir:
        updated_config['meta_dir'] = meta_dir
    
    print()
    return updated_config


def main() -> None:
    """
    Command-line interface for PDFIngestor with YAML configuration and interactive mode.
    """
    parser = argparse.ArgumentParser(
        description="Extract text and metadata from PDF files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Directory containing PDF files to process (overrides config and interactive input)"
    )
    
    parser.add_argument(
        "--text-dir",
        type=Path,
        help="Directory where extracted text files will be saved (overrides config and interactive input)"
    )
    
    parser.add_argument(
        "--meta-dir",
        type=Path,
        help="Directory where metadata JSON files will be saved (overrides config and interactive input)"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default="config.yaml",
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (use config defaults and CLI args only)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Get interactive input if not in non-interactive mode
        if not args.non_interactive and not any([args.input_dir, args.text_dir, args.meta_dir]):
            config = get_interactive_input(config)
        
        # Override with command line arguments
        if args.input_dir:
            config['input_dir'] = str(args.input_dir)
        if args.text_dir:
            config['text_dir'] = str(args.text_dir)
        if args.meta_dir:
            config['meta_dir'] = str(args.meta_dir)
        
        # Create and run the ingestor
        ingestor = PDFIngestor(config)
        ingestor.process_all()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Please ensure config.yaml exists in the current directory.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()