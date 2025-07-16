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
            
            // Fetch detailed concept information
            const response = await fetch(`/api/concepts/${conceptId}/neighbors`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderConceptDetails(data);
            
        } catch (error) {
            console.error('Failed to load concept details:', error);
            this.elements.conceptDetails.innerHTML = `<div class="error-text">Failed to load concept details: ${error.message}</div>`;
        }
    }

    /**
     * Render concept details in the panel
     */
    renderConceptDetails(data) {
        const concept = data.concept;
        const neighbors = data.neighbors;
        const relationships = data.relationships;
        
        const html = `
            <div class="concept-detail-item">
                <div class="detail-label">Name</div>
                <div class="detail-value">${this.escapeHtml(concept.name)}</div>
            </div>
            
            <div class="concept-detail-item">
                <div class="detail-label">Type</div>
                <div class="detail-value">
                    <span class="concept-type-badge" style="background-color: ${this.getConceptColor(concept.type)}">${concept.type}</span>
                </div>
            </div>
            
            <div class="concept-detail-item">
                <div class="detail-label">Frequency</div>
                <div class="detail-value">${concept.frequency || 0}</div>
            </div>
            
            <div class="concept-detail-item">
                <div class="detail-label">Confidence</div>
                <div class="detail-value">${(concept.confidence * 100).toFixed(1)}%</div>
            </div>
            
            ${concept.context ? `
            <div class="concept-detail-item">
                <div class="detail-label">Context</div>
                <div class="detail-value">${this.escapeHtml(concept.context)}</div>
            </div>
            ` : ''}
            
            ${concept.source_docs && concept.source_docs.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Source Documents</div>
                <div class="detail-value">
                    <ul class="source-docs-list">
                        ${concept.source_docs.map(doc => `<li>${this.escapeHtml(doc)}</li>`).join('')}
                    </ul>
                </div>
            </div>
            ` : ''}
            
            ${relationships.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Relationships (${relationships.length})</div>
                <div class="detail-value">
                    ${relationships.slice(0, 5).map(rel => `
                        <div style="margin-bottom: 8px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
                            <strong>${rel.type}</strong> (${(rel.confidence * 100).toFixed(0)}%)
                        </div>
                    `).join('')}
                    ${relationships.length > 5 ? `<div style="color: #666; font-size: 12px;">... and ${relationships.length - 5} more</div>` : ''}
                </div>
            </div>
            ` : ''}
            
            ${neighbors.length > 0 ? `
            <div class="concept-detail-item">
                <div class="detail-label">Related Concepts (${neighbors.length})</div>
                <div class="detail-value">
                    ${neighbors.slice(0, 8).map(neighbor => `
                        <div style="margin-bottom: 6px; cursor: pointer; color: #2196F3;" onclick="app.selectConceptByName('${this.escapeHtml(neighbor.name)}')">
                            ${this.escapeHtml(neighbor.name)} <small>(${neighbor.type})</small>
                        </div>
                    `).join('')}
                    ${neighbors.length > 8 ? `<div style="color: #666; font-size: 12px;">... and ${neighbors.length - 8} more</div>` : ''}
                </div>
            </div>
            ` : ''}
        `;
        
        this.elements.conceptDetails.innerHTML = html;
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