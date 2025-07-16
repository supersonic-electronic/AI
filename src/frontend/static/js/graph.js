/**
 * Graph visualization module using Cytoscape.js
 * 
 * This module handles all graph-related functionality including:
 * - Cytoscape.js initialization and configuration
 * - Graph data loading and rendering
 * - Node and edge styling
 * - Layout algorithms
 * - Interactive features (selection, hover, etc.)
 */

class GraphManager {
    constructor(containerId) {
        this.containerId = containerId;
        this.cy = null;
        this.graphData = null;
        this.colorScheme = this.getEnhancedColorScheme();
        this.selectedNode = null;
        this.eventHandlers = {
            onNodeSelect: [],
            onNodeUnselect: [],
            onNodeHover: [],
            onEdgeSelect: []
        };
    }

    /**
     * Enhanced color scheme matching backend implementation
     */
    getEnhancedColorScheme() {
        return {
            // Mathematical concepts - Blue family
            'equation': '#2196F3',      // Material Blue
            'formula': '#1976D2',       // Material Blue 700
            'variable': '#42A5F5',      // Material Blue 400
            'constant': '#64B5F6',      // Material Blue 300
            'function': '#90CAF9',      // Material Blue 200
            'matrix': '#BBDEFB',        // Material Blue 100
            'vector': '#E3F2FD',        // Material Blue 50
            'operator': '#1565C0',      // Material Blue 800
            'theorem': '#0D47A1',       // Material Blue 900
            'proof': '#0277BD',         // Light Blue 800
            
            // Financial concepts - Green/Orange family
            'portfolio': '#FF8A50',     // Warm orange
            'asset': '#4CAF50',         // Material Green
            'risk': '#E91E63',          // Material Pink
            'return': '#2E7D32',        // Material Green 800
            'optimization': '#9C27B0',  // Material Purple
            'model': '#FF5722',         // Material Deep Orange
            'strategy': '#795548',      // Material Brown
            'performance': '#607D8B',   // Material Blue Grey
            'metric': '#00BCD4',        // Material Cyan
            'constraint': '#FFC107',    // Material Amber
            
            // General concepts - Grey/Purple family
            'author': '#9E9E9E',        // Material Grey
            'paper': '#757575',         // Material Grey 600
            'methodology': '#673AB7',   // Material Deep Purple
            'algorithm': '#3F51B5',     // Material Indigo
            'parameter': '#009688',     // Material Teal
            'assumption': '#8BC34A',    // Material Light Green
            'conclusion': '#CDDC39',    // Material Lime
            
            // Semantic concepts - Warm family
            'definition': '#FF9800',    // Material Orange
            'example': '#FF5722',       // Material Deep Orange
            'application': '#795548',   // Material Brown
            'limitation': '#F44336',    // Material Red
            
            // Default color for unknown types
            'unknown': '#9E9E9E'        // Material Grey
        };
    }

    /**
     * Initialize Cytoscape.js with configuration
     */
    async initialize() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            throw new Error(`Container with id '${this.containerId}' not found`);
        }

        // Cytoscape.js configuration
        this.cy = cytoscape({
            container: container,
            
            // Styling
            style: this.getGraphStyles(),
            
            // Layout
            layout: {
                name: 'cose-bilkent',
                animate: true,
                animationDuration: 1000,
                randomize: true,
                nodeRepulsion: 4500,
                idealEdgeLength: 50,
                edgeElasticity: 0.45,
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,
                tilingPaddingVertical: 10,
                tilingPaddingHorizontal: 10
            },
            
            // Interaction options
            minZoom: 0.2,
            maxZoom: 3.0,
            wheelSensitivity: 0.1,
            motionBlur: true,
            motionBlurOpacity: 0.2,
            pixelRatio: 'auto'
        });

        // Set up event handlers
        this.setupEventHandlers();
        
        console.log('Graph manager initialized successfully');
        return this.cy;
    }

    /**
     * Get Cytoscape.js styles configuration
     */
    getGraphStyles() {
        return [
            // Node styles
            {
                selector: 'node',
                style: {
                    'background-color': (ele) => {
                        const nodeType = ele.data('type') || 'unknown';
                        return this.colorScheme[nodeType] || this.colorScheme['unknown'];
                    },
                    'label': 'data(name)',
                    'font-size': '12px',
                    'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                    'font-weight': '500',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'color': '#ffffff',
                    'text-outline-color': (ele) => {
                        const nodeType = ele.data('type') || 'unknown';
                        return this.colorScheme[nodeType] || this.colorScheme['unknown'];
                    },
                    'text-outline-width': '2px',
                    'width': (ele) => {
                        const frequency = ele.data('frequency') || 0;
                        return Math.max(30, Math.min(80, 30 + (frequency / 100)));
                    },
                    'height': (ele) => {
                        const frequency = ele.data('frequency') || 0;
                        return Math.max(30, Math.min(80, 30 + (frequency / 100)));
                    },
                    'border-width': '2px',
                    'border-color': '#ffffff',
                    'border-opacity': 0.8,
                    'opacity': 0.9,
                    'transition-property': 'background-color, border-color, opacity',
                    'transition-duration': '0.2s'
                }
            },
            
            // Selected node style
            {
                selector: 'node:selected',
                style: {
                    'border-color': '#FFD700',
                    'border-width': '4px',
                    'opacity': 1.0,
                    'z-index': 999
                }
            },
            
            // Hovered node style
            {
                selector: 'node:active',
                style: {
                    'overlay-color': '#000000',
                    'overlay-opacity': 0.1,
                    'overlay-padding': '10px'
                }
            },
            
            // Edge styles
            {
                selector: 'edge',
                style: {
                    'width': (ele) => {
                        const confidence = ele.data('confidence') || 0.5;
                        return Math.max(1, confidence * 4);
                    },
                    'line-color': '#cccccc',
                    'target-arrow-color': '#cccccc',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.6,
                    'label': '',  // Hide edge labels by default
                    'font-size': '10px',
                    'font-family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                    'text-rotation': 'autorotate',
                    'text-margin-y': '-10px',
                    'color': '#666666',
                    'transition-property': 'line-color, target-arrow-color, opacity, width',
                    'transition-duration': '0.2s'
                }
            },
            
            // Selected edge style
            {
                selector: 'edge:selected',
                style: {
                    'line-color': '#FF8A50',
                    'target-arrow-color': '#FF8A50',
                    'width': 4,
                    'opacity': 1.0,
                    'label': 'data(type)',
                    'z-index': 999
                }
            },
            
            // Highlighted edges (connected to selected node)
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#FF8A50',
                    'target-arrow-color': '#FF8A50',
                    'opacity': 0.8,
                    'width': 3
                }
            },
            
            // Dimmed elements (not related to selection)
            {
                selector: '.dimmed',
                style: {
                    'opacity': 0.3
                }
            },
            
            // Hidden elements
            {
                selector: '.hidden',
                style: {
                    'display': 'none'
                }
            }
        ];
    }

    /**
     * Set up event handlers for graph interactions
     */
    setupEventHandlers() {
        // Node selection
        this.cy.on('tap', 'node', (event) => {
            const node = event.target;
            this.selectNode(node);
        });

        // Background click (deselect)
        this.cy.on('tap', (event) => {
            if (event.target === this.cy) {
                this.deselectAll();
            }
        });

        // Node hover
        this.cy.on('mouseover', 'node', (event) => {
            const node = event.target;
            this.highlightNodeNeighborhood(node, true);
            this.triggerEvent('onNodeHover', node);
        });

        this.cy.on('mouseout', 'node', (event) => {
            this.highlightNodeNeighborhood(null, false);
        });

        // Edge selection
        this.cy.on('tap', 'edge', (event) => {
            const edge = event.target;
            this.selectEdge(edge);
        });

        // Double-click to focus on node
        this.cy.on('dbltap', 'node', (event) => {
            const node = event.target;
            this.focusOnNode(node);
        });

        // Context menu prevention
        this.cy.on('cxttap', (event) => {
            event.preventDefault();
        });
    }

    /**
     * Load and render graph data
     */
    async loadGraphData() {
        try {
            console.log('Loading graph data from API...');
            
            const response = await fetch('/api/graph');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.graphData = await response.json();
            console.log(`Loaded ${this.graphData.nodes.length} nodes and ${this.graphData.edges.length} edges`);
            
            // Add data to cytoscape
            this.cy.add(this.graphData.nodes);
            this.cy.add(this.graphData.edges);
            
            // Run layout
            const layout = this.cy.layout({
                name: 'cose-bilkent',
                animate: true,
                animationDuration: 1500,
                randomize: true,
                nodeRepulsion: 4500,
                idealEdgeLength: 60,
                edgeElasticity: 0.45,
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,
                tilingPaddingVertical: 15,
                tilingPaddingHorizontal: 15
            });
            
            layout.run();
            
            // Fit view after layout completes
            layout.on('layoutstop', () => {
                this.cy.fit();
                this.cy.center();
                console.log('Graph layout completed');
            });
            
            return this.graphData;
            
        } catch (error) {
            console.error('Failed to load graph data:', error);
            throw error;
        }
    }

    /**
     * Select a node and highlight its neighborhood
     */
    selectNode(node) {
        // Deselect previous selection
        this.cy.elements().removeClass('dimmed');
        
        // Select new node
        this.selectedNode = node;
        node.select();
        
        // Highlight neighborhood
        this.highlightNodeNeighborhood(node, true);
        
        // Trigger event
        this.triggerEvent('onNodeSelect', node);
    }

    /**
     * Deselect all nodes and edges
     */
    deselectAll() {
        this.cy.elements().unselect();
        this.cy.elements().removeClass('dimmed highlighted');
        this.selectedNode = null;
        this.triggerEvent('onNodeUnselect', null);
    }

    /**
     * Select an edge and show its details
     */
    selectEdge(edge) {
        edge.select();
        this.triggerEvent('onEdgeSelect', edge);
    }

    /**
     * Highlight a node's neighborhood
     */
    highlightNodeNeighborhood(node, highlight) {
        if (!node && !highlight) {
            // Remove all highlighting
            this.cy.elements().removeClass('highlighted dimmed');
            return;
        }

        if (highlight && node) {
            // Get neighborhood
            const neighborhood = node.neighborhood().add(node);
            
            // Dim all elements
            this.cy.elements().addClass('dimmed');
            
            // Highlight neighborhood
            neighborhood.removeClass('dimmed');
            node.connectedEdges().addClass('highlighted');
        }
    }

    /**
     * Focus camera on a specific node
     */
    focusOnNode(node, zoom = 2.0) {
        this.cy.animate({
            center: { eles: node },
            zoom: zoom
        }, {
            duration: 500,
            easing: 'ease-in-out'
        });
    }

    /**
     * Fit graph to view
     */
    fitToView(padding = 50) {
        this.cy.fit(this.cy.elements(), padding);
    }

    /**
     * Apply filters to hide/show elements
     */
    applyFilters(filters) {
        // Reset visibility
        this.cy.elements().removeClass('hidden');
        
        // Apply concept type filter
        if (filters.conceptType && filters.conceptType !== '') {
            this.cy.nodes().forEach(node => {
                if (node.data('type') !== filters.conceptType) {
                    node.addClass('hidden');
                    // Also hide connected edges
                    node.connectedEdges().addClass('hidden');
                }
            });
        }
        
        // Apply search filter
        if (filters.searchTerm && filters.searchTerm.trim() !== '') {
            const searchTerm = filters.searchTerm.toLowerCase();
            this.cy.nodes().forEach(node => {
                const name = (node.data('name') || '').toLowerCase();
                const description = (node.data('description') || '').toLowerCase();
                
                if (!name.includes(searchTerm) && !description.includes(searchTerm)) {
                    node.addClass('hidden');
                    node.connectedEdges().addClass('hidden');
                }
            });
        }
    }

    /**
     * Get node by ID
     */
    getNodeById(nodeId) {
        return this.cy.getElementById(nodeId);
    }

    /**
     * Get graph statistics
     */
    getStats() {
        if (!this.graphData) return null;
        
        return {
            nodes: this.graphData.nodes.length,
            edges: this.graphData.edges.length,
            visibleNodes: this.cy.nodes(':visible').length,
            visibleEdges: this.cy.edges(':visible').length,
            ...this.graphData.stats
        };
    }

    /**
     * Export graph as PNG
     */
    exportAsPNG(options = {}) {
        const defaults = {
            output: 'blob',
            bg: '#ffffff',
            full: true,
            scale: 2
        };
        
        return this.cy.png({ ...defaults, ...options });
    }

    /**
     * Export graph as SVG
     */
    exportAsSVG(options = {}) {
        const defaults = {
            output: 'blob',
            bg: '#ffffff',
            full: true
        };
        
        return this.cy.svg({ ...defaults, ...options });
    }

    /**
     * Download graph as image file
     */
    downloadGraph(format = 'png', filename = 'knowledge-graph') {
        const exportMethod = format === 'svg' ? 'exportAsSVG' : 'exportAsPNG';
        
        try {
            const blob = this[exportMethod]();
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `${filename}.${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            URL.revokeObjectURL(url);
            console.log(`Graph exported as ${format.toUpperCase()}`);
            
        } catch (error) {
            console.error(`Failed to export graph as ${format}:`, error);
            throw error;
        }
    }

    /**
     * Change graph layout
     */
    changeLayout(layoutName, options = {}) {
        const layoutConfigs = {
            'cose-bilkent': {
                name: 'cose-bilkent',
                animate: true,
                animationDuration: 1000,
                nodeRepulsion: 4500,
                idealEdgeLength: 50,
                edgeElasticity: 0.45,
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,
                tilingPaddingVertical: 10,
                tilingPaddingHorizontal: 10,
                ...options
            },
            'circle': {
                name: 'circle',
                animate: true,
                animationDuration: 1000,
                radius: Math.min(window.innerWidth, window.innerHeight) * 0.3,
                ...options
            },
            'grid': {
                name: 'grid',
                animate: true,
                animationDuration: 1000,
                rows: Math.ceil(Math.sqrt(this.cy.nodes().length)),
                ...options
            },
            'breadthfirst': {
                name: 'breadthfirst',
                animate: true,
                animationDuration: 1000,
                directed: true,
                padding: 30,
                spacingFactor: 1.5,
                ...options
            },
            'concentric': {
                name: 'concentric',
                animate: true,
                animationDuration: 1000,
                concentric: (node) => node.data('frequency') || 1,
                levelWidth: () => 2,
                padding: 30,
                ...options
            },
            'dagre': {
                name: 'dagre',
                animate: true,
                animationDuration: 1000,
                rankDir: 'TB',
                ranker: 'network-simplex',
                nodeSep: 50,
                rankSep: 50,
                ...options
            }
        };
        
        const layoutConfig = layoutConfigs[layoutName];
        if (!layoutConfig) {
            console.error(`Unknown layout: ${layoutName}`);
            return;
        }
        
        const layout = this.cy.layout(layoutConfig);
        layout.run();
        
        console.log(`Applied ${layoutName} layout`);
        return layout;
    }

    /**
     * Get available layouts
     */
    getAvailableLayouts() {
        return [
            { name: 'cose-bilkent', label: 'Force-Directed (Default)', description: 'Physics-based layout with good separation' },
            { name: 'circle', label: 'Circle', description: 'Arrange nodes in a circle' },
            { name: 'grid', label: 'Grid', description: 'Arrange nodes in a grid pattern' },
            { name: 'breadthfirst', label: 'Hierarchical', description: 'Tree-like hierarchical layout' },
            { name: 'concentric', label: 'Concentric', description: 'Concentric circles by importance' },
            { name: 'dagre', label: 'Directed Graph', description: 'Directed acyclic graph layout' }
        ];
    }

    /**
     * Add event listener
     */
    addEventListener(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].push(handler);
        }
    }

    /**
     * Remove event listener
     */
    removeEventListener(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }

    /**
     * Trigger event handlers
     */
    triggerEvent(eventType, data) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${eventType} handler:`, error);
                }
            });
        }
    }

    /**
     * Destroy the graph instance
     */
    destroy() {
        if (this.cy) {
            this.cy.destroy();
            this.cy = null;
        }
    }
}

// Export for use in other modules
window.GraphManager = GraphManager;