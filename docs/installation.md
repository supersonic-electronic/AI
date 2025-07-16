# Installation

This guide will help you install and set up the AI Knowledge Graph system.

## Prerequisites

- Python 3.9 or higher
- Poetry (recommended) or pip
- Git

### System Dependencies

Some extractors require additional system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev
```

**macOS:**
```bash
brew install libxml2 libxslt jpeg libpng
```

**Windows:**
Most dependencies will be handled by pip, but you may need Visual Studio Build Tools.

## Installation Methods

### Method 1: Using Poetry (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/supersonic-electronic/AI.git
   cd AI
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install
   ```

4. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

### Method 2: Using pip

1. **Clone the repository:**
   ```bash
   git clone https://github.com/supersonic-electronic/AI.git
   cd AI
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Copy the example configuration:**
   ```bash
   cp config.yaml.example config.yaml
   ```

2. **Edit the configuration file:**
   ```bash
   nano config.yaml  # or your preferred editor
   ```

3. **Set up API keys** (optional but recommended):
   - OpenAI API key for enhanced text processing
   - Mathpix API key for advanced formula recognition
   - Pinecone API key for cloud vector storage

## Verification

Test your installation:

```bash
# Using Poetry
poetry run python -m src.cli --help

# Using pip
python -m src.cli --help
```

You should see the CLI help message with available commands.

## Development Setup

For development, install additional dependencies:

```bash
# Using Poetry
poetry install --with dev

# Using pip
pip install -r requirements-dev.txt
```

Install pre-commit hooks:

```bash
pre-commit install
```

## Docker Installation (Alternative)

If you prefer using Docker:

1. **Build the image:**
   ```bash
   docker build -t ai-knowledge-graph .
   ```

2. **Run the container:**
   ```bash
   docker run -it --rm -v $(pwd)/data:/app/data ai-knowledge-graph
   ```

## Troubleshooting

### Common Issues

**ImportError: No module named 'fitz'**
```bash
pip install pymupdf
```

**Permission errors on Windows:**
Run your terminal as Administrator when installing.

**Missing system dependencies:**
Ensure all system packages are installed as shown in Prerequisites.

### Getting Help

If you encounter issues:

1. Check the [troubleshooting guide](troubleshooting.md)
2. Search existing [GitHub issues](https://github.com/supersonic-electronic/AI/issues)
3. Create a new issue with your error details

## Next Steps

After installation, proceed to the [Quick Start Guide](quickstart.md) to begin processing documents.