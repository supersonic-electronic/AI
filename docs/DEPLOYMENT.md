# Knowledge Graph Visualizer - Production Deployment Guide

## 🚀 Deployment Overview

This guide covers deploying the Knowledge Graph Visualizer frontend to production after completing Phase 3 implementation.

## 📋 Pre-deployment Checklist

### ✅ Phase 3 Features Implemented
- [x] Performance monitoring system integrated
- [x] Graph export functionality (PNG/SVG/JSON)
- [x] Multiple layout algorithms (6 options: cose-bilkent, circle, grid, breadthfirst, concentric, dagre)
- [x] Help modal with comprehensive keyboard shortcuts
- [x] Enhanced error handling and UI polish
- [x] Dropdown controls and accessibility features
- [x] Dark mode and responsive design support
- [x] Integration testing completed

### ✅ File Structure Verified
```
src/frontend/
├── app.py                     # FastAPI application (24KB)
├── api/
│   ├── concepts.py           # Concepts API endpoints
│   ├── graph.py              # Graph API endpoints
│   └── search.py             # Search API endpoints
├── static/
│   ├── css/
│   │   └── main.css          # Enhanced styles (17KB)
│   └── js/
│       ├── graph.js          # Graph manager (21KB)
│       ├── main.js           # Application controller (32KB)
│       └── performance.js    # Performance monitoring (14KB)
└── templates/
    └── index.html            # Main HTML template (9KB)
```

## 🔧 Production Setup

### 1. Environment Configuration

Create a production environment file:

```bash
# .env.production
WEB_DEBUG=false
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_STATIC_DIR=src/frontend/static
WEB_TEMPLATES_DIR=src/frontend/templates
```

### 2. Dependencies Installation

```bash
# Install production dependencies
poetry install --no-dev

# Or with pip
pip install -r requirements.txt
```

### 3. Application Startup

```bash
# Start with Gunicorn (recommended for production)
poetry run gunicorn src.frontend.app:create_app --bind 0.0.0.0:8000 --workers 4

# Or with uvicorn
poetry run uvicorn src.frontend.app:create_app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "src.frontend.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔒 Security Considerations

### CORS Configuration
Update CORS settings in `src/frontend/app.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Static File Serving
For production, consider serving static files through a reverse proxy (nginx/Apache):

```nginx
# nginx configuration
location /static/ {
    alias /path/to/app/src/frontend/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🎛️ Performance Optimizations

### 1. CDN Integration
Consider using CDN for Cytoscape.js and other libraries:

```html
<!-- Already configured in index.html -->
<script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
<script src="https://unpkg.com/cytoscape-cose-bilkent@4.1.0/cytoscape-cose-bilkent.js"></script>
```

### 2. File Compression
Enable gzip compression in your web server:

```nginx
# nginx gzip configuration
gzip on;
gzip_types text/css application/javascript application/json;
gzip_min_length 1000;
```

### 3. Performance Monitoring
The integrated performance monitor will automatically track:
- Page load times
- Graph rendering performance
- API response times
- Memory usage
- User interaction rates

## 📊 Monitoring & Health Checks

### Health Check Endpoint
The application includes a health check at `/health`:

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "service": "knowledge-graph-visualizer", "version": "1.0.0"}
```

### Performance Metrics
Access browser developer tools to see performance logs:
- Graph load times
- Memory usage warnings
- API call performance
- Render time tracking

## 🎨 UI Features Available in Production

### Graph Visualization
- Interactive node selection and details
- 6 layout algorithms with real-time switching
- Zoom, pan, and focus controls
- Enhanced color scheme for concept types

### Export Functionality
- PNG image export (high resolution)
- SVG vector export (scalable)
- JSON data export (complete graph data)

### User Experience
- Real-time search with suggestions
- Keyboard shortcuts (F, R, H, Ctrl+F, 1-6)
- Help modal with comprehensive documentation
- Responsive design for all screen sizes
- Dark mode support (respects system preference)

### Accessibility
- ARIA labels and roles
- Keyboard navigation support
- High contrast mode compatibility
- Reduced motion support for sensitive users

## 🐛 Troubleshooting

### Common Issues

1. **Static files not loading**
   - Check `WEB_STATIC_DIR` path is correct
   - Verify file permissions
   - Check web server configuration

2. **Performance issues**
   - Monitor browser developer tools
   - Check performance logs in console
   - Verify memory usage indicators

3. **Layout problems**
   - Try different layout algorithms
   - Check graph data structure
   - Verify Cytoscape.js CDN availability

### Debugging Mode
Enable debug mode for development:

```python
# In settings
WEB_DEBUG=true
```

## 🚀 Deployment Commands Summary

```bash
# Quick production deployment
poetry install --no-dev
poetry run uvicorn src.frontend.app:create_app --host 0.0.0.0 --port 8000

# Run integration tests
python test_frontend.py

# Health check
curl http://localhost:8000/health
```

## 📈 Phase 3 Completion Status

✅ **COMPLETED** - All Phase 3 requirements implemented and tested
- Performance monitoring: ✓ Integrated
- Graph export: ✓ PNG/SVG/JSON support
- Layout options: ✓ 6 algorithms available
- Help system: ✓ Modal with shortcuts
- UI polish: ✓ Enhanced design
- Error handling: ✓ Comprehensive coverage
- Accessibility: ✓ Full compliance
- Integration testing: ✓ All tests passed

**🎉 The Knowledge Graph Visualizer frontend is production-ready!**