# OCR Configuration Guide

This guide explains how to configure and use OCR services (Mathpix and OpenAI Vision) for mathematical formula extraction in the portfolio optimizer.

## OCR Services Overview

The system supports two OCR services for mathematical formula extraction:

1. **Mathpix** - Specialized for mathematical content (recommended)
2. **OpenAI Vision** - General-purpose vision model with math capabilities

## Configuration Options

### 1. Mathpix Configuration

Mathpix is the preferred OCR service for mathematical content due to its specialization in mathematical notation.

#### Step 1: Get Mathpix API Credentials

1. Visit [Mathpix](https://mathpix.com/) and create an account
2. Navigate to the API dashboard
3. Create a new application to get your `app_id` and `app_key`

#### Step 2: Configure in config.yaml

```yaml
# Mathpix SDK Configuration
mathpix_app_id: "your_mathpix_app_id_here"
mathpix_app_key: "your_mathpix_app_key_here"
mathpix_timeout: 30.0
mathpix_max_retries: 3
mathpix_retry_delay: 1.0

# Enable OCR fallback
math_ocr_fallback: true
```

#### Step 3: Set Environment Variables (Alternative)

```bash
export PORTFOLIO_OPTIMIZER_MATHPIX_APP_ID="your_app_id"
export PORTFOLIO_OPTIMIZER_MATHPIX_APP_KEY="your_app_key"
export PORTFOLIO_OPTIMIZER_MATH_OCR_FALLBACK="true"
```

### 2. OpenAI Vision Configuration

OpenAI Vision API can be used as a fallback or primary OCR service.

#### Step 1: Get OpenAI API Key

1. Visit [OpenAI](https://platform.openai.com/) and create an account
2. Navigate to API Keys section
3. Create a new API key

#### Step 2: Configure in config.yaml

```yaml
# OpenAI Configuration
openai_api_key: "your_openai_api_key_here"
openai_timeout: 60.0

# Enable OCR fallback
math_ocr_fallback: true
```

#### Step 3: Set Environment Variables (Alternative)

```bash
export PORTFOLIO_OPTIMIZER_OPENAI_API_KEY="your_openai_api_key"
export PORTFOLIO_OPTIMIZER_MATH_OCR_FALLBACK="true"
```

## Usage Examples

### Basic Usage with OCR

```bash
# Enable OCR fallback during ingestion
python -m src.cli ingest --math-ocr

# Or with specific configuration
python -m src.cli --config production-config.yaml ingest --math-ocr
```

### Configuration Priority

The system will attempt OCR in the following order:

1. **Mathpix** (if credentials are configured)
2. **OpenAI Vision** (if API key is configured)
3. **No OCR** (fallback to text-based detection only)

## Improved Mathematical Detection

### Enhanced Algorithm

The improved math detector (`improved_math_detector.py`) provides:

- **Reduced false positives** through stricter filtering
- **Better context analysis** for mathematical expressions
- **Higher precision** with increased detection thresholds
- **Rejection patterns** for common non-mathematical content

### Key Improvements

1. **Rejection Filters**:
   - Page numbers (e.g., "5", "Page 10")
   - Citations (e.g., "[1]", "[23]")
   - Isolated variables (e.g., "x", "y1")
   - Section headers (e.g., "1. Introduction")

2. **Enhanced Patterns**:
   - Complete equations with both sides
   - Mathematical expressions with operations
   - Specific fraction patterns
   - Matrix notation patterns

3. **Stricter Thresholds**:
   - Minimum threshold raised from 3 to 5
   - Length penalties for very short expressions
   - Context bonuses for multi-line expressions

### Using the Improved Detector

To use the improved math detector, modify your ingestion code:

```python
from src.ingestion.improved_math_detector import get_improved_math_detector

# In your PDF ingestion code
settings = Settings.from_env_and_yaml("config.yaml")
math_detector = get_improved_math_detector(settings)

# Use the improved detector
is_math, confidence, breakdown = math_detector.detect_mathematical_content(text)
```

## Configuration Examples

### Example 1: Mathpix Only

```yaml
# config.yaml
mathpix_app_id: "your_mathpix_app_id"
mathpix_app_key: "your_mathpix_app_key"
math_ocr_fallback: true
math_detection_threshold: 5  # Higher threshold for better precision
```

### Example 2: OpenAI Vision Only

```yaml
# config.yaml
openai_api_key: "your_openai_api_key"
math_ocr_fallback: true
math_detection_threshold: 5
```

### Example 3: Both Services (Recommended)

```yaml
# config.yaml
mathpix_app_id: "your_mathpix_app_id"
mathpix_app_key: "your_mathpix_app_key"
openai_api_key: "your_openai_api_key"
math_ocr_fallback: true
math_detection_threshold: 6  # Even higher threshold with dual OCR
```

## Performance Considerations

### API Limits and Costs

#### Mathpix
- **Free tier**: 1000 requests/month
- **Cost**: $0.004 per request after free tier
- **Rate limit**: 10 requests/second

#### OpenAI Vision
- **Cost**: $0.01 per image (up to 1024x1024)
- **Rate limit**: Depends on your account tier
- **Context**: Uses GPT-4 Vision Preview model

### Optimization Tips

1. **Use higher thresholds** to reduce unnecessary OCR calls
2. **Enable OCR only for low-confidence detections** (< 0.7)
3. **Batch process** documents to optimize API usage
4. **Monitor API usage** to avoid unexpected costs

## Troubleshooting

### Common Issues

1. **"mpxpy package not available"**
   ```bash
   poetry add mpxpy
   ```

2. **"OpenAI package not available"**
   ```bash
   poetry add openai
   ```

3. **API Key Errors**
   - Verify your API keys are correct
   - Check if your account has sufficient credits
   - Ensure environment variables are set correctly

4. **Timeout Issues**
   - Increase timeout values in configuration
   - Check your internet connection
   - Verify API service status

### Debug Mode

Enable debug logging to see OCR results:

```yaml
# config.yaml
log_level: "DEBUG"
```

Or via CLI:

```bash
python -m src.cli --verbose ingest --math-ocr
```

## Testing OCR Configuration

### Test Script

Create a test script to verify OCR setup:

```python
from src.settings import Settings
from src.ingestion.improved_math_detector import get_improved_math_detector

# Load settings
settings = Settings.from_env_and_yaml("config.yaml")

# Create detector
detector = get_improved_math_detector(settings)

# Test text
test_text = "E(R_p) = w'μ where μ is the mean return vector"
is_math, confidence, breakdown = detector.detect_mathematical_content(test_text)

print(f"Text: {test_text}")
print(f"Is mathematical: {is_math}")
print(f"Confidence: {confidence:.3f}")
print(f"Breakdown: {breakdown}")
```

### Integration Test

Test with actual PDF processing:

```bash
# Process a single PDF with OCR enabled
python -m src.cli ingest --math-ocr --input-dir ./test/single-pdf --verbose
```

## Best Practices

1. **Start with improved detection** before enabling OCR
2. **Use high confidence thresholds** (0.6+) for OCR fallback
3. **Monitor API costs** regularly
4. **Test with sample documents** before production use
5. **Keep API keys secure** and use environment variables
6. **Implement retry logic** for API failures
7. **Cache OCR results** to avoid repeated calls

## Security Considerations

- Never commit API keys to version control
- Use environment variables or secure key management
- Rotate API keys periodically
- Monitor API usage for suspicious activity
- Consider using API key restrictions where available