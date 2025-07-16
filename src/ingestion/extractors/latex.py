"""
LaTeX extractor using regex and text processing.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .base import BaseExtractor


class LaTeXExtractor(BaseExtractor):
    """
    LaTeX document extractor using text processing and regex.
    
    Extracts text and metadata from LaTeX files with configurable options
    for command handling, environment processing, and math extraction.
    """
    
    def __init__(self):
        """Initialize the LaTeX extractor."""
        self.content = ""
        self.commands = {}
        self.environments = {}
    
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle LaTeX files.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has .tex or .latex extension, False otherwise
        """
        return file_path.suffix.lower() in ['.tex', '.latex']
    
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """
        Extract text from a LaTeX file using regex processing.
        
        Args:
            file_path: Path to the LaTeX file
            config: Configuration dictionary
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If LaTeX cannot be opened or processed
        """
        try:
            # Read file with encoding detection
            encoding = config.get('latex_encoding', 'utf-8')
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    self.content = f.read()
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    self.content = f.read()
            
            # Process LaTeX content
            text = self._process_latex_content(config)
            
            # Clean and normalize text
            text = self._clean_text(text, config)
            
            return text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _process_latex_content(self, config: Dict[str, Any]) -> str:
        """
        Process LaTeX content to extract readable text.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Processed text content
        """
        content = self.content
        
        # Remove comments
        if config.get('remove_comments', True):
            content = self._remove_comments(content)
        
        # Process includes
        if config.get('process_includes', False):
            content = self._process_includes(content, config)
        
        # Extract and process environments
        if config.get('extract_environments', True):
            content = self._process_environments(content, config)
        
        # Process LaTeX commands
        if config.get('process_commands', True):
            content = self._process_commands(content, config)
        
        # Handle math expressions
        if config.get('process_math', True):
            content = self._process_math(content, config)
        
        # Process citations and references
        if config.get('process_citations', True):
            content = self._process_citations(content, config)
        
        # Remove remaining LaTeX artifacts
        content = self._remove_latex_artifacts(content, config)
        
        return content
    
    def _remove_comments(self, content: str) -> str:
        """
        Remove LaTeX comments from content.
        
        Args:
            content: LaTeX content
            
        Returns:
            Content with comments removed
        """
        # Remove comments (% to end of line), but not escaped %
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Find % that are not escaped
            comment_pos = -1
            escaped = False
            
            for i, char in enumerate(line):
                if char == '\\':
                    escaped = not escaped
                elif char == '%' and not escaped:
                    comment_pos = i
                    break
                else:
                    escaped = False
            
            if comment_pos >= 0:
                cleaned_lines.append(line[:comment_pos].rstrip())
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _process_includes(self, content: str, config: Dict[str, Any]) -> str:
        """
        Process LaTeX include statements.
        
        Args:
            content: LaTeX content
            config: Configuration dictionary
            
        Returns:
            Content with includes processed
        """
        # For now, just mark include statements
        # Full implementation would require file system access
        include_pattern = r'\\(?:input|include|subfile)\{([^}]+)\}'
        
        def replace_include(match):
            filename = match.group(1)
            return f"[INCLUDED FILE: {filename}]"
        
        return re.sub(include_pattern, replace_include, content)
    
    def _process_environments(self, content: str, config: Dict[str, Any]) -> str:
        """
        Process LaTeX environments.
        
        Args:
            content: LaTeX content
            config: Configuration dictionary
            
        Returns:
            Content with environments processed
        """
        # Extract environment configuration
        extract_envs = config.get('extract_environment_types', [
            'document', 'abstract', 'section', 'subsection', 'paragraph',
            'itemize', 'enumerate', 'description', 'quote', 'quotation',
            'figure', 'table', 'center', 'flushleft', 'flushright'
        ])
        
        skip_envs = config.get('skip_environment_types', [
            'tikzpicture', 'pgfpicture', 'pspicture'
        ])
        
        # Process environments
        env_pattern = r'\\begin\{([^}]+)\}(.*?)\\end\{\1\}'
        
        def process_environment(match):
            env_name = match.group(1)
            env_content = match.group(2)
            
            if env_name in skip_envs:
                return f"[{env_name.upper()} ENVIRONMENT SKIPPED]"
            
            if env_name in extract_envs or not extract_envs:
                # Process the environment content
                if env_name in ['itemize', 'enumerate', 'description']:
                    return self._process_list_environment(env_content, env_name)
                elif env_name in ['figure', 'table']:
                    return self._process_float_environment(env_content, env_name, config)
                else:
                    return env_content
            
            return f"[{env_name.upper()} ENVIRONMENT]"
        
        # Process environments (with DOTALL flag for multiline)
        return re.sub(env_pattern, process_environment, content, flags=re.DOTALL)
    
    def _process_list_environment(self, content: str, env_type: str) -> str:
        """
        Process list environments (itemize, enumerate, description).
        
        Args:
            content: Environment content
            env_type: Environment type
            
        Returns:
            Processed list content
        """
        # Convert \item to bullet points or numbers
        if env_type == 'itemize':
            content = re.sub(r'\\item\s*', '• ', content)
        elif env_type == 'enumerate':
            # Simple numbering (would need counter for accurate numbering)
            item_count = 0
            def replace_item(match):
                nonlocal item_count
                item_count += 1
                return f"{item_count}. "
            content = re.sub(r'\\item\s*', replace_item, content)
        elif env_type == 'description':
            content = re.sub(r'\\item\[([^\]]+)\]\s*', r'\1: ', content)
        
        return content
    
    def _process_float_environment(self, content: str, env_type: str, config: Dict[str, Any]) -> str:
        """
        Process float environments (figure, table).
        
        Args:
            content: Environment content
            env_type: Environment type
            config: Configuration dictionary
            
        Returns:
            Processed float content
        """
        processed_content = []
        
        # Extract caption
        caption_match = re.search(r'\\caption\{([^}]+)\}', content)
        if caption_match:
            caption = caption_match.group(1)
            processed_content.append(f"[{env_type.upper()} CAPTION: {caption}]")
        
        # Extract label
        label_match = re.search(r'\\label\{([^}]+)\}', content)
        if label_match:
            label = label_match.group(1)
            processed_content.append(f"[LABEL: {label}]")
        
        # For figures, note graphics
        if env_type == 'figure':
            graphics_matches = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', content)
            for graphic in graphics_matches:
                processed_content.append(f"[IMAGE: {graphic}]")
        
        return '\n'.join(processed_content)
    
    def _process_commands(self, content: str, config: Dict[str, Any]) -> str:
        """
        Process LaTeX commands.
        
        Args:
            content: LaTeX content
            config: Configuration dictionary
            
        Returns:
            Content with commands processed
        """
        # Define command processing rules
        command_rules = {
            # Text formatting
            r'\\textbf\{([^}]+)\}': r'\1',  # Bold
            r'\\textit\{([^}]+)\}': r'\1',  # Italic
            r'\\emph\{([^}]+)\}': r'\1',    # Emphasis
            r'\\texttt\{([^}]+)\}': r'\1',  # Typewriter
            r'\\underline\{([^}]+)\}': r'\1', # Underline
            
            # Sectioning
            r'\\title\{([^}]+)\}': r'TITLE: \1\n',
            r'\\author\{([^}]+)\}': r'AUTHOR: \1\n',
            r'\\date\{([^}]+)\}': r'DATE: \1\n',
            r'\\chapter\{([^}]+)\}': r'\n\nCHAPTER: \1\n',
            r'\\section\{([^}]+)\}': r'\n\nSECTION: \1\n',
            r'\\subsection\{([^}]+)\}': r'\n\nSUBSECTION: \1\n',
            r'\\subsubsection\{([^}]+)\}': r'\n\nSUBSUBSECTION: \1\n',
            r'\\paragraph\{([^}]+)\}': r'\n\nPARAGRAPH: \1\n',
            
            # Special characters
            r'\\&': '&',
            r'\\%': '%',
            r'\\\$': '$',
            r'\\#': '#',
            r'\\_': '_',
            r'\\{': '{',
            r'\\}': '}',
            r'\\\\': '\n',  # Line break
            
            # Quotes
            r"``": '"',
            r"''": '"',
            r"`": "'",
            r"'": "'",
            
            # Dashes
            r'---': '—',  # Em dash
            r'--': '–',   # En dash
        }
        
        # Apply command rules
        for pattern, replacement in command_rules.items():
            content = re.sub(pattern, replacement, content)
        
        # Handle remaining simple commands (remove them)
        if config.get('remove_unknown_commands', True):
            # Remove commands with no arguments
            content = re.sub(r'\\[a-zA-Z]+\*?(?!\{)', '', content)
            
            # Remove commands with arguments (keep content)
            content = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', content)
        
        return content
    
    def _process_math(self, content: str, config: Dict[str, Any]) -> str:
        """
        Process mathematical expressions.
        
        Args:
            content: LaTeX content
            config: Configuration dictionary
            
        Returns:
            Content with math processed
        """
        math_mode = config.get('math_processing_mode', 'placeholder')
        
        if math_mode == 'remove':
            # Remove all math
            content = re.sub(r'\$\$.*?\$\$', '', content, flags=re.DOTALL)  # Display math
            content = re.sub(r'\$.*?\$', '', content)  # Inline math
            content = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '', content, flags=re.DOTALL)
            content = re.sub(r'\\begin\{align\}.*?\\end\{align\}', '', content, flags=re.DOTALL)
        elif math_mode == 'placeholder':
            # Replace with placeholders
            content = re.sub(r'\$\$.*?\$\$', '[DISPLAY MATH]', content, flags=re.DOTALL)
            content = re.sub(r'\$.*?\$', '[MATH]', content)
            content = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '[EQUATION]', content, flags=re.DOTALL)
            content = re.sub(r'\\begin\{align\}.*?\\end\{align\}', '[ALIGNED EQUATIONS]', content, flags=re.DOTALL)
        else:  # 'preserve'
            # Keep math as-is
            pass
        
        return content
    
    def _process_citations(self, content: str, config: Dict[str, Any]) -> str:
        """
        Process citations and references.
        
        Args:
            content: LaTeX content
            config: Configuration dictionary
            
        Returns:
            Content with citations processed
        """
        citation_mode = config.get('citation_processing_mode', 'expand')
        
        if citation_mode == 'remove':
            # Remove citations
            content = re.sub(r'\\cite\{[^}]+\}', '', content)
            content = re.sub(r'\\ref\{[^}]+\}', '', content)
        elif citation_mode == 'expand':
            # Expand citations
            content = re.sub(r'\\cite\{([^}]+)\}', r'[CITE: \1]', content)
            content = re.sub(r'\\ref\{([^}]+)\}', r'[REF: \1]', content)
        else:  # 'preserve'
            # Keep as-is
            pass
        
        return content
    
    def _remove_latex_artifacts(self, content: str, config: Dict[str, Any]) -> str:
        """
        Remove remaining LaTeX artifacts.
        
        Args:
            content: LaTeX content
            config: Configuration dictionary
            
        Returns:
            Cleaned content
        """
        # Remove remaining backslash commands
        content = re.sub(r'\\[a-zA-Z]+\*?', '', content)
        
        # Remove extra braces
        content = re.sub(r'\{([^{}]*)\}', r'\1', content)
        
        # Remove LaTeX-specific punctuation patterns
        content = re.sub(r'~', ' ', content)  # Non-breaking space
        
        return content
    
    def _clean_text(self, text: str, config: Dict[str, Any]) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            config: Configuration dictionary
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        if config.get('normalize_whitespace', True):
            # Replace multiple spaces with single space
            text = re.sub(r' +', ' ', text)
            # Replace multiple newlines with double newline
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            # Remove leading/trailing whitespace from lines
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(lines)
        
        # Remove empty lines if configured
        if config.get('remove_empty_lines', True):
            lines = [line for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
        
        return text.strip()
    
    def extract_metadata(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a LaTeX file.
        
        Args:
            file_path: Path to the LaTeX file
            config: Configuration dictionary
            
        Returns:
            Dictionary containing LaTeX metadata
            
        Raises:
            Exception: If LaTeX cannot be opened or metadata cannot be extracted
        """
        try:
            # If content not already loaded, load it
            if not self.content:
                encoding = config.get('latex_encoding', 'utf-8')
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        self.content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        self.content = f.read()
            
            metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
            }
            
            # Extract document metadata
            metadata.update(self._extract_document_metadata())
            
            # Extract bibliography information
            if config.get('extract_bibliography', True):
                bib_info = self._extract_bibliography_info()
                if bib_info:
                    metadata.update(bib_info)
            
            # Extract package information
            if config.get('extract_packages', True):
                packages = self._extract_packages()
                if packages:
                    metadata['packages'] = packages
            
            # Extract document structure
            if config.get('extract_structure', True):
                structure = self._extract_structure()
                if structure:
                    metadata.update(structure)
            
            # Remove empty values
            metadata = {k: v for k, v in metadata.items() if v}
            
            return metadata
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise
    
    def _extract_document_metadata(self) -> Dict[str, Any]:
        """
        Extract document metadata from LaTeX preamble.
        
        Returns:
            Dictionary with document metadata
        """
        metadata = {}
        
        # Extract title, author, date
        title_match = re.search(r'\\title\{([^}]+)\}', self.content)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        author_match = re.search(r'\\author\{([^}]+)\}', self.content)
        if author_match:
            metadata['author'] = author_match.group(1).strip()
        
        date_match = re.search(r'\\date\{([^}]+)\}', self.content)
        if date_match:
            metadata['date'] = date_match.group(1).strip()
        
        # Extract document class
        documentclass_match = re.search(r'\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}', self.content)
        if documentclass_match:
            metadata['document_class'] = documentclass_match.group(1)
        
        return metadata
    
    def _extract_bibliography_info(self) -> Dict[str, Any]:
        """
        Extract bibliography information.
        
        Returns:
            Dictionary with bibliography information
        """
        bib_info = {}
        
        # Extract bibliography files
        bib_files = re.findall(r'\\bibliography\{([^}]+)\}', self.content)
        if bib_files:
            bib_info['bibliography_files'] = bib_files
        
        # Extract bibliography style
        bib_style_match = re.search(r'\\bibliographystyle\{([^}]+)\}', self.content)
        if bib_style_match:
            bib_info['bibliography_style'] = bib_style_match.group(1)
        
        # Count citations
        citations = re.findall(r'\\cite\{([^}]+)\}', self.content)
        if citations:
            # Split multiple citations
            all_citations = []
            for citation in citations:
                all_citations.extend([c.strip() for c in citation.split(',')])
            bib_info['citation_count'] = len(all_citations)
            bib_info['unique_citations'] = len(set(all_citations))
        
        return bib_info
    
    def _extract_packages(self) -> List[str]:
        """
        Extract LaTeX packages used.
        
        Returns:
            List of package names
        """
        packages = []
        
        # Find usepackage commands
        package_matches = re.findall(r'\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}', self.content)
        for match in package_matches:
            # Handle multiple packages in one command
            packages.extend([pkg.strip() for pkg in match.split(',')])
        
        return sorted(list(set(packages)))
    
    def _extract_structure(self) -> Dict[str, Any]:
        """
        Extract document structure information.
        
        Returns:
            Dictionary with structure information
        """
        structure = {}
        
        # Count sectioning commands
        sections = {
            'chapters': len(re.findall(r'\\chapter\{', self.content)),
            'sections': len(re.findall(r'\\section\{', self.content)),
            'subsections': len(re.findall(r'\\subsection\{', self.content)),
            'subsubsections': len(re.findall(r'\\subsubsection\{', self.content)),
        }
        
        # Only include non-zero counts
        structure['section_counts'] = {k: v for k, v in sections.items() if v > 0}
        
        # Count environments
        env_matches = re.findall(r'\\begin\{([^}]+)\}', self.content)
        if env_matches:
            env_counts = {}
            for env in env_matches:
                env_counts[env] = env_counts.get(env, 0) + 1
            structure['environment_counts'] = env_counts
        
        # Count figures and tables
        figure_count = len(re.findall(r'\\begin\{figure\}', self.content))
        table_count = len(re.findall(r'\\begin\{table\}', self.content))
        
        if figure_count > 0:
            structure['figure_count'] = figure_count
        if table_count > 0:
            structure['table_count'] = table_count
        
        return structure
    
    @property
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this extractor supports.
        
        Returns:
            List containing '.tex' and '.latex'
        """
        return ['.tex', '.latex']
    
    @property
    def extractor_name(self) -> str:
        """
        Human-readable name of this extractor.
        
        Returns:
            Name of the LaTeX extractor
        """
        return "LaTeX Extractor (Regex-based)"