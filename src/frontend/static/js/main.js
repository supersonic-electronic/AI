/**
 * Main application controller
 * 
 * This module handles:
 * - Application initialization
 * - UI interactions and controls
 * - Search functionality
 * - Concept details panel
 * - Graph filters and legend
 * - Status updates and performance monitoring
 */

class KnowledgeGraphApp {
    constructor() {
        this.graphManager = null;
        this.currentFilters = {
            conceptType: '',
            searchTerm: ''
        };
        this.searchTimeout = null;
        this.performanceStart = null;
        this.conceptTypes = [];
        this.performanceMonitor = null;
        
        // UI elements
        this.elements = {
            loading: document.getElementById('loading'),
            searchInput: document.getElementById('search-input'),
            searchSuggestions: document.getElementById('search-suggestions'),
            refreshBtn: document.getElementById('refresh-btn'),
            fitBtn: document.getElementById('fit-btn'),
            conceptTypeFilter: document.getElementById('concept-type-filter'),
            detailsPanel: document.getElementById('details-panel'),
            conceptDetails: document.getElementById('concept-details'),
            closeDetailsBtn: document.getElementById('close-details'),
            statusText: document.getElementById('status-text'),
            performanceInfo: document.getElementById('performance-info'),
            conceptsCount: document.getElementById('concepts-count'),
            relationshipsCount: document.getElementById('relationships-count'),
            legend: document.getElementById('legend'),
            layoutBtn: document.getElementById('layout-btn'),
            layoutMenu: document.getElementById('layout-menu'),
            exportBtn: document.getElementById('export-btn'),
            exportMenu: document.getElementById('export-menu'),
            exportPng: document.getElementById('export-png'),
            exportSvg: document.getElementById('export-svg'),
            exportData: document.getElementById('export-data'),
            helpBtn: document.getElementById('help-btn'),
            helpModal: document.getElementById('help-modal'),
            closeHelpBtn: document.getElementById('close-help'),
            modalOverlay: document.getElementById('modal-overlay')
        };
    }

    /**
     * Initialize the application
     */
    async initialize() {
        try {
            console.log('Initializing Knowledge Graph Visualizer...');
            this.performanceStart = performance.now();
            
            // Initialize performance monitoring
            this.performanceMonitor = new PerformanceMonitor();
            this.performanceMonitor.start();
            
            this.updateStatus('Initializing graph engine...');
            
            // Initialize graph manager
            this.graphManager = new GraphManager('graph');
            await this.graphManager.initialize();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadGraph();
            
            // Setup UI components
            await this.setupUI();
            
            const loadTime = performance.now() - this.performanceStart;
            this.updateStatus('Ready');
            this.updatePerformance(`Loaded in ${loadTime.toFixed(0)}ms`);
            
            console.log('Application initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.updateStatus('Failed to load application', 'error');
            this.showError('Failed to initialize the knowledge graph visualizer', error);
        }
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Graph events
        this.graphManager.addEventListener('onNodeSelect', (node) => {
            this.showConceptDetails(node);
        });
        
        this.graphManager.addEventListener('onNodeUnselect', () => {
            this.hideConceptDetails();
        });
        
        this.graphManager.addEventListener('onNodeHover', (node) => {
            this.updateStatus(`Hovering: ${node.data('name')}`);
        });
        
        // Search input
        this.elements.searchInput.addEventListener('input', (event) => {
            this.handleSearch(event.target.value);
        });
        
        this.elements.searchInput.addEventListener('focus', () => {
            this.showSearchSuggestions();
        });
        
        this.elements.searchInput.addEventListener('blur', () => {
            // Delay hiding to allow click on suggestions
            setTimeout(() => this.hideSearchSuggestions(), 200);
        });
        
        // Control buttons
        this.elements.refreshBtn.addEventListener('click', () => {
            this.refreshGraph();
        });
        
        this.elements.fitBtn.addEventListener('click', () => {
            this.fitGraphToView();
        });
        
        // Concept type filter
        this.elements.conceptTypeFilter.addEventListener('change', (event) => {
            this.currentFilters.conceptType = event.target.value;
            this.applyFilters();
        });
        
        // Details panel
        this.elements.closeDetailsBtn.addEventListener('click', () => {
            this.hideConceptDetails();
            this.graphManager.deselectAll();
        });
        
        // Layout controls
        this.elements.layoutBtn.addEventListener('click', () => {
            this.toggleDropdown('layout');
        });
        
        // Export controls
        this.elements.exportBtn.addEventListener('click', () => {
            this.toggleDropdown('export');
        });
        
        this.elements.exportPng.addEventListener('click', () => {
            this.exportGraph('png');
        });
        
        this.elements.exportSvg.addEventListener('click', () => {
            this.exportGraph('svg');
        });
        
        this.elements.exportData.addEventListener('click', () => {
            this.exportData();
        });
        
        // Help modal
        this.elements.helpBtn.addEventListener('click', () => {
            this.showHelpModal();
        });
        
        this.elements.closeHelpBtn.addEventListener('click', () => {
            this.hideHelpModal();
        });
        
        this.elements.modalOverlay.addEventListener('click', () => {
            this.hideHelpModal();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboard(event);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            if (this.graphManager && this.graphManager.cy) {
                this.graphManager.cy.resize();
            }
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (event) => {
            this.closeDropdowns(event);
        });
        
        // Enhanced tooltip functionality (FR4)
        this.setupTooltips();
    }
    
    /**
     * Setup enhanced graph node tooltips (FR4: Interactive Graph Node Tooltips)
     */
    setupTooltips() {
        // Create tooltip element
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'enhanced-tooltip';
        document.body.appendChild(this.tooltip);
        
        // Tooltip state management
        this.tooltipState = {
            visible: false,
            timeout: null,
            cache: new Map(),
            currentNode: null
        };
        
        // Enhanced hover events with delay (FR4.1)
        this.graphManager.addEventListener('onNodeHover', (node) => {
            this.handleNodeHover(node);
        });
        
        this.graphManager.addEventListener('onNodeUnhover', () => {
            this.handleNodeUnhover();
        });
        
        // Hide tooltip on graph pan/zoom for performance (FR4.3)
        if (this.graphManager.cy) {
            this.graphManager.cy.on('pan zoom', () => {
                this.hideTooltip();
            });
        }
    }
    
    /**
     * Handle node hover with 300ms delay (FR4.1)
     */
    handleNodeHover(node) {
        // Clear any existing timeout
        if (this.tooltipState.timeout) {
            clearTimeout(this.tooltipState.timeout);
        }
        
        // Set 300ms delay before showing tooltip
        this.tooltipState.timeout = setTimeout(() => {
            this.showEnhancedTooltip(node);
        }, 300);
        
        this.tooltipState.currentNode = node;
    }
    
    /**
     * Handle node unhover
     */
    handleNodeUnhover() {
        // Clear timeout to prevent showing tooltip
        if (this.tooltipState.timeout) {
            clearTimeout(this.tooltipState.timeout);
            this.tooltipState.timeout = null;
        }
        
        // Hide tooltip immediately
        this.hideTooltip();
        this.tooltipState.currentNode = null;
    }
    
    /**
     * Show enhanced tooltip with metadata (FR4.1, FR4.2)
     */
    async showEnhancedTooltip(node) {
        try {
            const nodeId = node.id();
            
            // Check cache first (FR4.3)
            let tooltipData = this.tooltipState.cache.get(nodeId);
            
            if (!tooltipData) {
                // Lazy-load tooltip content (FR4.3)
                tooltipData = await this.loadTooltipData(node);
                this.tooltipState.cache.set(nodeId, tooltipData);
                
                // Limit cache size to prevent memory issues
                if (this.tooltipState.cache.size > 100) {
                    const firstKey = this.tooltipState.cache.keys().next().value;
                    this.tooltipState.cache.delete(firstKey);
                }
            }
            
            // Generate tooltip HTML
            const tooltipHTML = this.generateTooltipHTML(tooltipData);
            this.tooltip.innerHTML = tooltipHTML;
            
            // Position tooltip responsively (FR4.2)
            this.positionTooltip(node);
            
            // Show tooltip
            this.tooltip.classList.add('visible');
            this.tooltipState.visible = true;
            
            // Render LaTeX if present (FR4.2)
            this.renderTooltipMath();
            
        } catch (error) {
            console.warn('Failed to show tooltip:', error);
        }
    }
    
    /**
     * Load tooltip data for a node (FR4.3 - lazy loading)
     */
    async loadTooltipData(node) {
        const nodeData = node.data();
        
        // Extract enhanced metadata including DBpedia fields
        const tooltipData = {
            name: nodeData.name || 'Unknown',
            type: nodeData.type || 'unknown',
            complexity_level: nodeData.complexity_level || 'intermediate',
            domain: nodeData.domain || 'finance',
            prerequisites: nodeData.prerequisites || [],
            confidence: nodeData.confidence || 1.0,
            frequency: nodeData.frequency || 0,
            latex: nodeData.latex || null,
            description: nodeData.description || null,
            // DBpedia-specific fields
            dbpedia_enriched: nodeData.dbpedia_enriched || false,
            dbpedia_uri: nodeData.dbpedia_uri || null,
            dbpedia_confidence: nodeData.dbpedia_confidence || 0,
            external_source: nodeData.external_source || 'local',
            aliases: nodeData.aliases || [],
            properties: nodeData.properties || {},
            // Enhanced external metadata fields
            categories: (nodeData.properties && nodeData.properties.categories) || [],
            types: (nodeData.properties && nodeData.properties.types) || [],
            examples: nodeData.examples || [],
            applications: nodeData.applications || [],
            related_formulas: nodeData.related_formulas || [],
            related_external_concepts: (nodeData.properties && nodeData.properties.related_external_concepts) || [],
            
            // New enhanced metadata from API
            external_categories: nodeData.external_categories || [],
            external_types: nodeData.external_types || [],
            external_type_names: nodeData.external_type_names || [],
            external_urls: nodeData.external_urls || {},
            external_comments: nodeData.external_comments || '',
            external_redirect_labels: nodeData.external_redirect_labels || [],
            
            // Wikidata enrichment
            wikidata_enriched: nodeData.wikidata_enriched || false,
            wikidata_instance_of: nodeData.wikidata_instance_of || [],
            wikidata_subclass_of: nodeData.wikidata_subclass_of || [],
            
            // Source document context
            source_documents: nodeData.source_documents || [],
            source_title: nodeData.source_title || '',
            source_authors: nodeData.source_authors || [],
            source_publication_year: nodeData.source_publication_year || '',
            source_context_snippet: nodeData.source_context_snippet || '',
            primary_source_doc: nodeData.primary_source_doc || '',
            concept_frequency: nodeData.concept_frequency || 0,
            
            // Legacy source document info
            source_document: nodeData.source_document || null,
            source_page: nodeData.source_page || null,
            context: nodeData.context || null
        };
        
        return tooltipData;
    }
    
    /**
     * Generate tooltip HTML content (FR4.1, FR4.2) with DBpedia integration
     */
    generateTooltipHTML(data) {
        const { 
            name, type, complexity_level, domain, prerequisites, confidence, frequency, latex, description,
            dbpedia_enriched, dbpedia_uri, dbpedia_confidence, external_source, aliases,
            source_document, source_page, context,
            // Enhanced metadata
            wikidata_enriched, external_categories, external_urls, source_title, source_authors, 
            source_publication_year, primary_source_doc, concept_frequency, external_comments
        } = data;
        
        // Dual source badges
        let sourceBadges = '';
        if (dbpedia_enriched && wikidata_enriched) {
            sourceBadges = '<div class="tooltip-source-badge enriched-badge">DBpedia</div><div class="tooltip-source-badge enriched-badge">Wikidata</div>';
        } else if (dbpedia_enriched) {
            sourceBadges = '<div class="tooltip-source-badge enriched-badge">DBpedia Enriched</div>';
        } else if (wikidata_enriched) {
            sourceBadges = '<div class="tooltip-source-badge enriched-badge">Wikidata Enriched</div>';
        } else {
            sourceBadges = '<div class="tooltip-source-badge local-badge">Local Document</div>';
        }
        
        return `
            <div class="tooltip-header">
                <div class="tooltip-title">${this.escapeHtml(name)}</div>
                <div class="tooltip-type">${this.escapeHtml(type)}</div>
                ${sourceBadges}
            </div>
            <div class="tooltip-content">
                <div class="tooltip-row">
                    <span class="tooltip-label">Complexity:</span>
                    <span class="tooltip-value complexity-${complexity_level}">${complexity_level}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Domain:</span>
                    <span class="tooltip-value">${this.escapeHtml(domain)}</span>
                </div>
                ${confidence < 1.0 ? `
                <div class="tooltip-row">
                    <span class="tooltip-label">Confidence:</span>
                    <span class="tooltip-value">${(confidence * 100).toFixed(0)}%</span>
                </div>` : ''}
                ${frequency > 0 ? `
                <div class="tooltip-row">
                    <span class="tooltip-label">Frequency:</span>
                    <span class="tooltip-value">${frequency}</span>
                </div>` : ''}
                ${prerequisites.length > 0 ? `
                <div class="tooltip-row">
                    <span class="tooltip-label">Prerequisites:</span>
                    <span class="tooltip-value">${prerequisites.slice(0, 3).map(p => this.escapeHtml(p)).join(', ')}${prerequisites.length > 3 ? '...' : ''}</span>
                </div>` : ''}
                
                ${this.generateDBpediaSection(data)}
                ${this.generateLocalSourceSection(data)}
                
                ${latex ? `
                <div class="tooltip-latex">
                    <div class="tooltip-label">Formula:</div>
                    <div class="tooltip-math">\\(${latex}\\)</div>
                </div>` : ''}
                ${description ? `
                <div class="tooltip-description">
                    ${this.escapeHtml(description.substring(0, 150))}${description.length > 150 ? '...' : ''}
                </div>` : ''}
            </div>
        `;
    }
    
    /**
     * Generate DBpedia-specific section for tooltip
     */
    generateDBpediaSection(data) {
        const { dbpedia_enriched, dbpedia_uri, dbpedia_confidence, external_source, aliases, 
                categories, types, examples, applications, related_formulas, related_external_concepts,
                // Enhanced metadata
                wikidata_enriched, external_categories, external_urls, external_comments,
                wikidata_instance_of, wikidata_subclass_of } = data;
        
        if (!dbpedia_enriched && external_source !== 'dbpedia') {
            return '';
        }
        
        let section = '<div class="tooltip-section tooltip-dbpedia-section">';
        
        if (dbpedia_uri) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">DBpedia URI:</span>
                    <span class="tooltip-value">
                        <a href="${dbpedia_uri}" target="_blank" rel="noopener noreferrer" class="tooltip-link">
                            View on DBpedia ↗
                        </a>
                    </span>
                </div>`;
        }
        
        if (dbpedia_confidence > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">DBpedia Confidence:</span>
                    <span class="tooltip-value">${(dbpedia_confidence * 100).toFixed(0)}%</span>
                </div>`;
        }
        
        if (aliases && aliases.length > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Aliases:</span>
                    <span class="tooltip-value">${aliases.slice(0, 3).map(a => this.escapeHtml(a)).join(', ')}${aliases.length > 3 ? '...' : ''}</span>
                </div>`;
        }
        
        // Enhanced metadata fields
        if (categories && categories.length > 0) {
            const categoryList = categories.slice(0, 4).map(cat => {
                // Extract readable category name from URI
                const categoryName = cat.includes('/') ? cat.split('/').pop().replace(/_/g, ' ') : cat;
                return this.escapeHtml(categoryName);
            }).join(', ');
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Categories:</span>
                    <span class="tooltip-value">${categoryList}${categories.length > 4 ? '...' : ''}</span>
                </div>`;
        }
        
        if (types && types.length > 0) {
            const typeList = types.slice(0, 3).map(type => {
                const typeName = type.includes('/') ? type.split('/').pop().replace(/_/g, ' ') : type;
                return this.escapeHtml(typeName);
            }).join(', ');
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Types:</span>
                    <span class="tooltip-value">${typeList}${types.length > 3 ? '...' : ''}</span>
                </div>`;
        }
        
        if (examples && examples.length > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Examples:</span>
                    <span class="tooltip-value">${examples.slice(0, 2).map(ex => this.escapeHtml(ex)).join('; ')}${examples.length > 2 ? '...' : ''}</span>
                </div>`;
        }
        
        if (applications && applications.length > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Applications:</span>
                    <span class="tooltip-value">${applications.slice(0, 2).map(app => this.escapeHtml(app)).join(', ')}${applications.length > 2 ? '...' : ''}</span>
                </div>`;
        }
        
        if (related_formulas && related_formulas.length > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Related Formulas:</span>
                    <span class="tooltip-value">${related_formulas.slice(0, 2).map(formula => this.escapeHtml(formula)).join(', ')}${related_formulas.length > 2 ? '...' : ''}</span>
                </div>`;
        }
        
        if (related_external_concepts && related_external_concepts.length > 0) {
            const relatedList = related_external_concepts.slice(0, 3).map(concept => {
                const conceptName = concept.includes('/') ? concept.split('/').pop().replace(/_/g, ' ') : concept;
                return `<span class="related-concept">${this.escapeHtml(conceptName)}</span>`;
            }).join(', ');
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Related Concepts:</span>
                    <span class="tooltip-value">${relatedList}${related_external_concepts.length > 3 ? '...' : ''}</span>
                </div>`;
        }
        
        // Enhanced external metadata from new API fields
        if (external_categories && external_categories.length > 0) {
            const categoryList = external_categories.slice(0, 4).map(cat => {
                const categoryName = cat.includes('/') ? cat.split('/').pop().replace(/_/g, ' ') : cat;
                return this.escapeHtml(categoryName);
            }).join(', ');
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">External Categories:</span>
                    <span class="tooltip-value">${categoryList}${external_categories.length > 4 ? '...' : ''}</span>
                </div>`;
        }
        
        // External URLs section
        if (external_urls && Object.keys(external_urls).length > 0) {
            const links = [];
            if (external_urls.dbpedia) {
                links.push(`<a href="${external_urls.dbpedia}" target="_blank" class="tooltip-link">DBpedia ↗</a>`);
            }
            if (external_urls.wikidata) {
                links.push(`<a href="${external_urls.wikidata}" target="_blank" class="tooltip-link">Wikidata ↗</a>`);
            }
            if (links.length > 0) {
                section += `
                    <div class="tooltip-row">
                        <span class="tooltip-label">External Links:</span>
                        <span class="tooltip-value">${links.join(' | ')}</span>
                    </div>`;
            }
        }
        
        // Wikidata semantic metadata
        if (wikidata_enriched && wikidata_instance_of && wikidata_instance_of.length > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Instance Of:</span>
                    <span class="tooltip-value">${wikidata_instance_of.slice(0, 3).map(i => this.escapeHtml(i)).join(', ')}</span>
                </div>`;
        }
        
        if (external_comments) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Description:</span>
                    <span class="tooltip-value">${this.escapeHtml(external_comments.substring(0, 100))}${external_comments.length > 100 ? '...' : ''}</span>
                </div>`;
        }
        
        section += '</div>';
        return section;
    }
    
    /**
     * Generate local source section for tooltip
     */
    generateLocalSourceSection(data) {
        const { external_source, source_document, source_page, context,
                // Enhanced source document metadata
                source_title, source_authors, source_publication_year, primary_source_doc, 
                concept_frequency, source_context_snippet } = data;
        
        // Show local source section if we have any source document metadata
        if (external_source === 'dbpedia' || (!source_document && !context && !source_title && !primary_source_doc)) {
            return '';
        }
        
        let section = '<div class="tooltip-section tooltip-local-section">';
        
        if (source_document) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Document:</span>
                    <span class="tooltip-value">${this.escapeHtml(source_document)}</span>
                </div>`;
        }
        
        if (source_page) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Page:</span>
                    <span class="tooltip-value">${source_page}</span>
                </div>`;
        }
        
        // Enhanced source document metadata
        if (source_title) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Title:</span>
                    <span class="tooltip-value">${this.escapeHtml(source_title)}</span>
                </div>`;
        }
        
        if (source_authors && source_authors.length > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Authors:</span>
                    <span class="tooltip-value">${source_authors.slice(0, 5).map(a => this.escapeHtml(a)).join(', ')}${source_authors.length > 5 ? ` (+${source_authors.length - 5} more)` : ''}</span>
                </div>`;
        }
        
        if (source_publication_year) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Year:</span>
                    <span class="tooltip-value">${source_publication_year}</span>
                </div>`;
        }
        
        if (concept_frequency > 0) {
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Frequency:</span>
                    <span class="tooltip-value">${concept_frequency.toLocaleString()} occurrences</span>
                </div>`;
        }
        
        // Show multiple source documents if available
        if (data.source_documents && data.source_documents.length > 1) {
            const sourceList = data.source_documents.slice(0, 3).map(doc => {
                // Clean up filename for display
                const cleanName = doc.replace('.txt', '').replace('_', ' ');
                return this.escapeHtml(cleanName);
            }).join(', ');
            section += `
                <div class="tooltip-row">
                    <span class="tooltip-label">Sources:</span>
                    <span class="tooltip-value">${sourceList}${data.source_documents.length > 3 ? ` (+${data.source_documents.length - 3} more)` : ''}</span>
                </div>`;
        }
        
        if (context) {
            section += `
                <div class="tooltip-context">
                    <div class="tooltip-label">Context:</div>
                    <div class="tooltip-context-text">${this.escapeHtml(context.substring(0, 100))}${context.length > 100 ? '...' : ''}</div>
                </div>`;
        }
        
        section += '</div>';
        return section;
    }
    
    /**
     * Position tooltip responsively to avoid viewport overflow (FR4.2)
     */
    positionTooltip(node) {
        const renderedNode = node.renderedBoundingBox();
        const container = this.graphManager.cy.container();
        const containerRect = container.getBoundingClientRect();
        
        // Calculate initial position (above and to the right of node)
        let left = containerRect.left + renderedNode.x2 + 10;
        let top = containerRect.top + renderedNode.y1 - 10;
        
        // Get tooltip dimensions
        this.tooltip.style.visibility = 'hidden';
        this.tooltip.style.display = 'block';
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        // Adjust position to avoid viewport overflow
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // Horizontal overflow check
        if (left + tooltipRect.width > viewportWidth) {
            left = containerRect.left + renderedNode.x1 - tooltipRect.width - 10;
        }
        
        // Vertical overflow check
        if (top + tooltipRect.height > viewportHeight) {
            top = containerRect.top + renderedNode.y2 + 10;
        }
        
        // Ensure tooltip doesn't go off-screen
        left = Math.max(5, Math.min(left, viewportWidth - tooltipRect.width - 5));
        top = Math.max(5, Math.min(top, viewportHeight - tooltipRect.height - 5));
        
        // Apply position
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.visibility = 'visible';
    }
    
    /**
     * Render LaTeX math in tooltip (FR4.2)
     */
    renderTooltipMath() {
        if (window.MathJax && window.MathJax.typesetPromise) {
            // Use MathJax 3.x API
            window.MathJax.typesetPromise([this.tooltip]).catch((err) => {
                console.warn('MathJax rendering failed:', err);
            });
        } else if (window.MathJax && window.MathJax.Hub) {
            // Fallback for MathJax 2.x
            window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub, this.tooltip]);
        }
    }
    
    /**
     * Hide tooltip
     */
    hideTooltip() {
        this.tooltip.classList.remove('visible');
        this.tooltipState.visible = false;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Load graph data and render
     */
    async loadGraph() {
        try {
            this.updateStatus('Loading graph data...');
            this.showLoading(true);
            
            const graphData = await this.graphManager.loadGraphData();
            
            // Update statistics
            this.updateStatistics(graphData.stats);
            
            this.showLoading(false);
            this.updateStatus('Graph loaded successfully');
            
            return graphData;
            
        } catch (error) {
            this.showLoading(false);
            this.updateStatus('Failed to load graph data', 'error');
            throw error;
        }
    }

    /**
     * Setup UI components after data is loaded
     */
    async setupUI() {
        try {
            // Load concept types for filter
            await this.loadConceptTypes();
            
            // Generate legend
            this.generateLegend();
            
            // Setup layout menu
            this.setupLayoutMenu();
            
            // Set initial focus
            this.elements.searchInput.focus();
            
        } catch (error) {
            console.error('Failed to setup UI:', error);
        }
    }

    /**
     * Load concept types for filtering
     */
    async loadConceptTypes() {
        try {
            const response = await fetch('/api/search/types');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.conceptTypes = data.types;
            
            // Populate filter dropdown
            this.elements.conceptTypeFilter.innerHTML = '<option value="">All Types</option>';
            
            data.types.forEach(typeInfo => {
                const option = document.createElement('option');
                option.value = typeInfo.type;
                option.textContent = `${typeInfo.type} (${typeInfo.count})`;
                this.elements.conceptTypeFilter.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to load concept types:', error);
        }
    }

    /**
     * Generate color legend
     */
    generateLegend() {
        if (!this.graphManager) return;
        
        const colorScheme = this.graphManager.getEnhancedColorScheme();
        const legendContainer = this.elements.legend;
        
        // Clear existing legend
        legendContainer.innerHTML = '';
        
        // Create legend items for concept types that exist in the data
        const existingTypes = new Set();
        if (this.graphManager.graphData) {
            this.graphManager.graphData.nodes.forEach(node => {
                existingTypes.add(node.data.type);
            });
        }
        
        existingTypes.forEach(type => {
            if (type && colorScheme[type]) {
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                
                const colorBox = document.createElement('div');
                colorBox.className = 'legend-color';
                colorBox.style.backgroundColor = colorScheme[type];
                
                const label = document.createElement('span');
                label.className = 'legend-label';
                label.textContent = type.charAt(0).toUpperCase() + type.slice(1);
                
                legendItem.appendChild(colorBox);
                legendItem.appendChild(label);
                legendContainer.appendChild(legendItem);
                
                // Make legend items clickable to filter
                legendItem.addEventListener('click', () => {
                    this.elements.conceptTypeFilter.value = type;
                    this.currentFilters.conceptType = type;
                    this.applyFilters();
                });
                
                legendItem.style.cursor = 'pointer';
                legendItem.title = `Click to filter by ${type}`;
            }
        });
    }

    /**
     * Handle search input
     */
    handleSearch(searchTerm) {
        // Clear existing timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.currentFilters.searchTerm = searchTerm;
            this.applyFilters();
            
            if (searchTerm.length >= 2) {
                this.loadSearchSuggestions(searchTerm);
            } else {
                this.hideSearchSuggestions();
            }
        }, 300);
    }

    /**
     * Load and display search suggestions
     */
    async loadSearchSuggestions(query) {
        try {
            const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}&limit=8`);
            if (!response.ok) return;
            
            const data = await response.json();
            this.displaySearchSuggestions(data.suggestions);
            
        } catch (error) {
            console.error('Failed to load search suggestions:', error);
        }
    }

    /**
     * Display search suggestions
     */
    displaySearchSuggestions(suggestions) {
        const container = this.elements.searchSuggestions;
        container.innerHTML = '';
        
        if (suggestions.length === 0) {
            this.hideSearchSuggestions();
            return;
        }
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            
            const text = document.createElement('span');
            text.textContent = suggestion.text;
            
            const type = document.createElement('small');
            type.textContent = ` (${suggestion.type})`;
            type.style.color = '#999';
            
            item.appendChild(text);
            item.appendChild(type);
            
            item.addEventListener('click', () => {
                this.selectSearchSuggestion(suggestion.text);
            });
            
            container.appendChild(item);
        });
        
        this.showSearchSuggestions();
    }

    /**
     * Select a search suggestion
     */
    selectSearchSuggestion(text) {
        this.elements.searchInput.value = text;
        this.currentFilters.searchTerm = text;
        this.applyFilters();
        this.hideSearchSuggestions();
        
        // Try to find and select the concept
        const matchingNode = this.findConceptByName(text);
        if (matchingNode) {
            this.graphManager.selectNode(matchingNode);
            this.graphManager.focusOnNode(matchingNode);
        }
    }

    /**
     * Find concept node by name
     */
    findConceptByName(name) {
        if (!this.graphManager || !this.graphManager.cy) return null;
        
        const nodes = this.graphManager.cy.nodes();
        for (let i = 0; i < nodes.length; i++) {
            const node = nodes[i];
            if (node.data('name').toLowerCase() === name.toLowerCase()) {
                return node;
            }
        }
        return null;
    }

    /**
     * Show/hide search suggestions
     */
    showSearchSuggestions() {
        this.elements.searchSuggestions.style.display = 'block';
    }

    hideSearchSuggestions() {
        this.elements.searchSuggestions.style.display = 'none';
    }

    /**
     * Apply current filters to the graph
     */
    applyFilters() {
        if (!this.graphManager) return;
        
        this.graphManager.applyFilters(this.currentFilters);
        
        // Update statistics
        const stats = this.graphManager.getStats();
        if (stats) {
            this.updateVisibleCounts(stats.visibleNodes, stats.visibleEdges);
        }
        
        // Update status
        const activeFilters = [];
        if (this.currentFilters.conceptType) {
            activeFilters.push(`type: ${this.currentFilters.conceptType}`);
        }
        if (this.currentFilters.searchTerm) {
            activeFilters.push(`search: "${this.currentFilters.searchTerm}"`);
        }
        
        if (activeFilters.length > 0) {
            this.updateStatus(`Filtered by ${activeFilters.join(', ')}`);
        } else {
            this.updateStatus('No filters applied');
        }
    }

    /**
     * Show concept details in the side panel
     */
    async showConceptDetails(node) {
        const conceptId = node.data('id');
        
        try {
            // Show panel
            this.elements.detailsPanel.classList.add('visible');
            
            // Show loading in panel
            this.elements.conceptDetails.innerHTML = '<div class="loading-text">Loading concept details...</div>';
            
            // Fetch detailed concept information using the new API endpoint
            const response = await fetch(`/api/concepts/${conceptId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const conceptData = await response.json();
            this.renderConceptDetails(conceptData);
            
        } catch (error) {
            console.error('Failed to load concept details:', error);
            this.elements.conceptDetails.innerHTML = `<div class="error-text">Failed to load concept details: ${error.message}</div>`;
        }
    }

    /**
     * Render concept details in the panel
     */
    renderConceptDetails(concept) {
        // Build the enhanced concept details HTML with all new fields
        const html = `
            <div class="concept-detail-item">
                <div class="detail-label">Name</div>
                <div class="detail-value concept-name">${this.escapeHtml(concept.name)}</div>
            </div>
            
            <div class="concept-detail-item">
                <div class="detail-label">Type</div>
                <div class="detail-value">
                    <span class="concept-type-badge" style="background-color: ${this.getConceptColor(concept.type)};">${concept.type}</span>
                </div>
            </div>
            
            ${concept.definition ? `
            <div class="concept-detail-item">
                <div class="detail-label">Definition</div>
                <div class="detail-value tex2jax_process">${this.escapeHtml(concept.definition)}</div>
            </div>
            ` : ''}
            
            ${concept.description ? `
            <div class="concept-detail-item">
                <div class="detail-label">Description</div>
                <div class="detail-value tex2jax_process">${this.escapeHtml(concept.description)}</div>
            </div>
            ` : ''}
            
            ${concept.latex ? `
            <div class="concept-detail-item">
                <div class="detail-label">Mathematical Expression</div>
                <div class="detail-value tex2jax_process math-expression">$$${concept.latex}$$</div>
            </div>
            ` : ''}
            
            ${concept.notation ? `
            <div class="concept-detail-item">
                <div class="detail-label">Notation</div>
                <div class="detail-value tex2jax_process">${this.escapeHtml(concept.notation)}</div>
            </div>
            ` : ''}
            
            ${concept.related_formulas && concept.related_formulas.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Related Formulas</div>
                <div class="detail-value">
                    ${concept.related_formulas.map(formula => `
                        <div class="formula-item tex2jax_process">$${formula}$</div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${concept.examples && concept.examples.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Examples</div>
                <div class="detail-value">
                    <ul class="concept-list">
                        ${concept.examples.map(example => `<li class="tex2jax_process">${this.escapeHtml(example)}</li>`).join('')}
                    </ul>
                </div>
            </div>
            ` : ''}
            
            ${concept.applications && concept.applications.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Applications</div>
                <div class="detail-value">
                    <ul class="concept-list">
                        ${concept.applications.map(app => `<li>${this.escapeHtml(app)}</li>`).join('')}
                    </ul>
                </div>
            </div>
            ` : ''}
            
            ${concept.prerequisites && concept.prerequisites.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Prerequisites</div>
                <div class="detail-value">
                    <div class="tag-container">
                        ${concept.prerequisites.map(prereq => `<span class="concept-tag">${this.escapeHtml(prereq)}</span>`).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            <div class="concept-detail-item">
                <div class="detail-label">Confidence</div>
                <div class="detail-value">${(concept.confidence * 100).toFixed(1)}%</div>
            </div>
            
            ${concept.complexity_level ? `
            <div class="concept-detail-item">
                <div class="detail-label">Complexity Level</div>
                <div class="detail-value">
                    <span class="complexity-badge complexity-${concept.complexity_level}">${concept.complexity_level}</span>
                </div>
            </div>
            ` : ''}
            
            ${concept.domain ? `
            <div class="concept-detail-item">
                <div class="detail-label">Domain</div>
                <div class="detail-value">
                    <span class="domain-badge">${this.escapeHtml(concept.domain)}</span>
                </div>
            </div>
            ` : ''}
            
            ${concept.keywords && concept.keywords.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Keywords</div>
                <div class="detail-value">
                    <div class="tag-container">
                        ${concept.keywords.map(keyword => `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${concept.external_links && Object.keys(concept.external_links).length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">External Links</div>
                <div class="detail-value">
                    ${Object.entries(concept.external_links).map(([source, url]) => `
                        <div class="external-link">
                            <a href="${this.escapeHtml(url)}" target="_blank" rel="noopener noreferrer">
                                ${this.escapeHtml(source)} <span class="external-icon">↗</span>
                            </a>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
            
            ${concept.related_concepts && concept.related_concepts.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Related Concepts (${concept.related_concepts.length})</div>
                <div class="detail-value">
                    ${concept.related_concepts.slice(0, 8).map(related => `
                        <div class="related-concept" onclick="app.selectConceptByName('${this.escapeHtml(related.name)}')">
                            <span class="related-name">${this.escapeHtml(related.name)}</span>
                            <small class="related-type">(${related.type})</small>
                            <small class="related-relationship">${related.relationship_type}</small>
                        </div>
                    `).join('')}
                    ${concept.related_concepts.length > 8 ? `<div class="more-indicator">... and ${concept.related_concepts.length - 8} more</div>` : ''}
                </div>
            </div>
            ` : ''}
            
            ${concept.source_document ? `
            <div class="concept-detail-item">
                <div class="detail-label">Source Document</div>
                <div class="detail-value source-info">
                    <div>${this.escapeHtml(concept.source_document)}</div>
                    ${concept.source_page ? `<small>Page ${concept.source_page}</small>` : ''}
                </div>
            </div>
            ` : ''}
            
            ${concept.created_at ? `
            <div class="concept-detail-item">
                <div class="detail-label">Created</div>
                <div class="detail-value timestamp">${new Date(concept.created_at).toLocaleDateString()}</div>
            </div>
            ` : ''}
        `;
        
        // Set the HTML content
        this.elements.conceptDetails.innerHTML = html;
        
        // Process LaTeX content with MathJax
        this.processLatexContent();
    }

    /**
     * Process LaTeX content with MathJax
     */
    processLatexContent() {
        // Check if MathJax is available
        if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
            // Process only the concept details panel to avoid reprocessing the entire page
            MathJax.typesetPromise([this.elements.conceptDetails]).then(() => {
                console.log('LaTeX content processed successfully');
            }).catch((error) => {
                console.error('MathJax processing failed:', error);
            });
        } else {
            console.warn('MathJax not available for LaTeX rendering');
        }
    }

    /**
     * Hide concept details panel
     */
    hideConceptDetails() {
        this.elements.detailsPanel.classList.remove('visible');
    }

    /**
     * Get color for concept type
     */
    getConceptColor(type) {
        if (!this.graphManager) return '#9E9E9E';
        return this.graphManager.getEnhancedColorScheme()[type] || '#9E9E9E';
    }

    /**
     * Select concept by name (used by details panel)
     */
    selectConceptByName(name) {
        const node = this.findConceptByName(name);
        if (node) {
            this.graphManager.selectNode(node);
            this.graphManager.focusOnNode(node);
        }
    }

    /**
     * Refresh the entire graph
     */
    async refreshGraph() {
        try {
            this.updateStatus('Refreshing graph...');
            this.hideConceptDetails();
            
            // Clear cache
            await fetch('/api/graph/cache/clear', { method: 'POST' });
            
            // Reload graph
            this.graphManager.cy.elements().remove();
            await this.loadGraph();
            await this.setupUI();
            
            this.updateStatus('Graph refreshed');
            
        } catch (error) {
            console.error('Failed to refresh graph:', error);
            this.updateStatus('Failed to refresh graph', 'error');
        }
    }

    /**
     * Fit graph to view
     */
    fitGraphToView() {
        if (this.graphManager) {
            this.graphManager.fitToView();
            this.updateStatus('Fitted to view');
        }
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboard(event) {
        // Escape key - deselect/close panels
        if (event.key === 'Escape') {
            this.graphManager.deselectAll();
            this.hideConceptDetails();
            this.hideSearchSuggestions();
        }
        
        // Ctrl/Cmd + F - focus search
        if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
            event.preventDefault();
            this.elements.searchInput.focus();
            this.elements.searchInput.select();
        }
        
        // F - fit to view
        if (event.key === 'f' && !event.ctrlKey && !event.metaKey) {
            this.fitGraphToView();
        }
        
        // R - refresh
        if (event.key === 'r' && !event.ctrlKey && !event.metaKey) {
            this.refreshGraph();
        }
    }

    /**
     * Update status bar
     */
    updateStatus(message, type = 'info') {
        this.elements.statusText.textContent = message;
        this.elements.statusText.className = `status-${type}`;
    }

    /**
     * Update performance information
     */
    updatePerformance(info) {
        this.elements.performanceInfo.textContent = info;
    }

    /**
     * Update statistics display
     */
    updateStatistics(stats) {
        this.elements.conceptsCount.textContent = stats.total_concepts || 0;
        this.elements.relationshipsCount.textContent = stats.total_relationships || 0;
    }

    /**
     * Update visible counts (after filtering)
     */
    updateVisibleCounts(visibleNodes, visibleEdges) {
        this.elements.conceptsCount.textContent = `${visibleNodes} / ${this.graphManager.graphData.nodes.length}`;
        this.elements.relationshipsCount.textContent = `${visibleEdges} / ${this.graphManager.graphData.edges.length}`;
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        this.elements.loading.style.display = show ? 'flex' : 'none';
    }

    /**
     * Show error message
     */
    showError(message, error = null) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <h3>Error</h3>
            <p>${this.escapeHtml(message)}</p>
            ${error ? `<details><summary>Technical Details</summary><pre>${this.escapeHtml(error.toString())}</pre></details>` : ''}
            <button onclick="this.parentElement.remove()">Close</button>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 10000);
    }

    /**
     * Setup layout menu
     */
    setupLayoutMenu() {
        if (!this.graphManager) return;
        
        const layouts = this.graphManager.getAvailableLayouts();
        const menu = this.elements.layoutMenu;
        
        menu.innerHTML = '';
        
        layouts.forEach(layout => {
            const item = document.createElement('button');
            item.className = 'dropdown-item';
            item.textContent = layout.label;
            item.title = layout.description;
            
            item.addEventListener('click', () => {
                this.changeLayout(layout.name);
                this.closeDropdowns();
            });
            
            menu.appendChild(item);
        });
    }

    /**
     * Change graph layout
     */
    changeLayout(layoutName) {
        if (!this.graphManager) return;
        
        try {
            this.updateStatus(`Applying ${layoutName} layout...`);
            const startTime = performance.now();
            
            const layout = this.graphManager.changeLayout(layoutName);
            
            if (layout) {
                layout.on('layoutstop', () => {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    if (this.performanceMonitor) {
                        this.performanceMonitor.recordRenderTime('layout', startTime, endTime, this.graphManager.cy.elements().length);
                    }
                    
                    this.updateStatus(`Applied ${layoutName} layout (${duration.toFixed(0)}ms)`);
                });
            }
            
        } catch (error) {
            console.error('Failed to change layout:', error);
            this.updateStatus('Failed to change layout', 'error');
        }
    }

    /**
     * Export graph as image
     */
    exportGraph(format) {
        if (!this.graphManager) return;
        
        try {
            this.updateStatus(`Exporting graph as ${format.toUpperCase()}...`);
            
            const filename = `knowledge-graph-${new Date().toISOString().slice(0, 10)}`;
            this.graphManager.downloadGraph(format, filename);
            
            this.updateStatus(`Graph exported as ${format.toUpperCase()}`);
            this.closeDropdowns();
            
        } catch (error) {
            console.error(`Failed to export graph as ${format}:`, error);
            this.updateStatus(`Failed to export graph`, 'error');
        }
    }

    /**
     * Export graph data as JSON
     */
    exportData() {
        try {
            this.updateStatus('Exporting graph data...');
            
            const data = {
                graphData: this.graphManager.graphData,
                stats: this.graphManager.getStats(),
                exportedAt: new Date().toISOString(),
                version: '1.0'
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `knowledge-graph-data-${new Date().toISOString().slice(0, 10)}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            URL.revokeObjectURL(url);
            
            this.updateStatus('Graph data exported');
            this.closeDropdowns();
            
        } catch (error) {
            console.error('Failed to export data:', error);
            this.updateStatus('Failed to export data', 'error');
        }
    }

    /**
     * Toggle dropdown menu
     */
    toggleDropdown(type) {
        const dropdowns = document.querySelectorAll('.dropdown');
        
        // Close all other dropdowns
        dropdowns.forEach(dropdown => {
            if (!dropdown.querySelector(`#${type}-btn`)) {
                dropdown.classList.remove('open');
            }
        });
        
        // Toggle the requested dropdown
        const targetDropdown = document.querySelector(`#${type}-btn`).parentElement;
        targetDropdown.classList.toggle('open');
    }

    /**
     * Close all dropdowns
     */
    closeDropdowns(event = null) {
        if (event && event.target.closest('.dropdown')) {
            return; // Don't close if clicking inside a dropdown
        }
        
        const dropdowns = document.querySelectorAll('.dropdown');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('open');
        });
    }

    /**
     * Show help modal
     */
    showHelpModal() {
        this.elements.helpModal.classList.add('visible');
        this.elements.modalOverlay.classList.add('visible');
        
        // Focus management for accessibility
        this.elements.closeHelpBtn.focus();
    }

    /**
     * Hide help modal
     */
    hideHelpModal() {
        this.elements.helpModal.classList.remove('visible');
        this.elements.modalOverlay.classList.remove('visible');
        
        // Return focus to help button
        this.elements.helpBtn.focus();
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboard(event) {
        // Escape key - deselect/close panels
        if (event.key === 'Escape') {
            this.graphManager.deselectAll();
            this.hideConceptDetails();
            this.hideSearchSuggestions();
            this.hideHelpModal();
            this.closeDropdowns();
        }
        
        // Ctrl/Cmd + F - focus search
        if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
            event.preventDefault();
            this.elements.searchInput.focus();
            this.elements.searchInput.select();
        }
        
        // F - fit to view
        if (event.key === 'f' && !event.ctrlKey && !event.metaKey && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            this.fitGraphToView();
        }
        
        // R - refresh
        if (event.key === 'r' && !event.ctrlKey && !event.metaKey && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            this.refreshGraph();
        }
        
        // H - help
        if (event.key === 'h' && !event.ctrlKey && !event.metaKey && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            this.showHelpModal();
        }
        
        // 1-6 - change layouts
        if (/^[1-6]$/.test(event.key) && !event.ctrlKey && !event.metaKey && event.target.tagName !== 'INPUT') {
            event.preventDefault();
            const layouts = this.graphManager.getAvailableLayouts();
            const layoutIndex = parseInt(event.key) - 1;
            if (layouts[layoutIndex]) {
                this.changeLayout(layouts[layoutIndex].name);
            }
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize application when DOM is ready
let app;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        app = new KnowledgeGraphApp();
        await app.initialize();
        
        // Make app globally available for debugging
        window.app = app;
        
    } catch (error) {
        console.error('Failed to start application:', error);
        
        // Show fallback error message
        const loading = document.getElementById('loading');
        if (loading) {
            loading.innerHTML = `
                <div style="text-align: center; color: #f44336;">
                    <h3>Failed to Load</h3>
                    <p>The knowledge graph visualizer failed to initialize.</p>
                    <p style="font-size: 12px; color: #666;">Check the browser console for details.</p>
                    <button onclick="location.reload()" style="margin-top: 16px; padding: 8px 16px;">Retry</button>
                </div>
            `;
        }
    }
});