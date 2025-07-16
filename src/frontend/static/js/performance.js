/**
 * Performance monitoring and optimization utilities
 * 
 * This module provides:
 * - Performance metrics collection
 * - Memory usage monitoring
 * - API response time tracking
 * - Graph rendering optimization
 * - Browser capability detection
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoad: null,
            graphLoad: null,
            apiCalls: [],
            renderTimes: [],
            memoryUsage: [],
            userInteractions: []
        };
        
        this.observers = {
            performance: [],
            memory: []
        };
        
        this.config = {
            maxApiCallHistory: 50,
            maxRenderTimeHistory: 100,
            memoryCheckInterval: 5000,
            performanceReportInterval: 30000
        };
        
        this.startTime = performance.now();
        this.isMonitoring = false;
    }

    /**
     * Start performance monitoring
     */
    start() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        console.log('Performance monitoring started');
        
        // Record page load time
        this.recordPageLoad();
        
        // Start memory monitoring
        this.startMemoryMonitoring();
        
        // Start periodic reporting
        this.startPeriodicReporting();
        
        // Monitor user interactions
        this.monitorUserInteractions();
        
        // Monitor API calls
        this.monitorApiCalls();
    }

    /**
     * Stop performance monitoring
     */
    stop() {
        this.isMonitoring = false;
        console.log('Performance monitoring stopped');
    }

    /**
     * Record page load performance
     */
    recordPageLoad() {
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
            const domContentLoadedTime = timing.domContentLoadedEventEnd - timing.navigationStart;
            const firstPaintTime = this.getFirstPaintTime();
            
            this.metrics.pageLoad = {
                total: pageLoadTime,
                domContentLoaded: domContentLoadedTime,
                firstPaint: firstPaintTime,
                timestamp: Date.now()
            };
            
            console.log(`Page load performance:`, this.metrics.pageLoad);
        }
    }

    /**
     * Get first paint time
     */
    getFirstPaintTime() {
        if (window.performance && window.performance.getEntriesByType) {
            const paintEntries = window.performance.getEntriesByType('paint');
            const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
            return firstPaint ? firstPaint.startTime : null;
        }
        return null;
    }

    /**
     * Record graph loading time
     */
    recordGraphLoad(startTime, endTime, nodeCount, edgeCount) {
        const loadTime = endTime - startTime;
        
        this.metrics.graphLoad = {
            loadTime,
            nodeCount,
            edgeCount,
            nodesPerSecond: nodeCount / (loadTime / 1000),
            timestamp: Date.now()
        };
        
        console.log(`Graph load performance:`, this.metrics.graphLoad);
        this.notifyObservers('performance', this.metrics.graphLoad);
    }

    /**
     * Record API call performance
     */
    recordApiCall(url, method, startTime, endTime, success, responseSize = null) {
        const callTime = endTime - startTime;
        
        const apiCall = {
            url,
            method,
            duration: callTime,
            success,
            responseSize,
            timestamp: Date.now()
        };
        
        this.metrics.apiCalls.push(apiCall);
        
        // Keep only recent API calls
        if (this.metrics.apiCalls.length > this.config.maxApiCallHistory) {
            this.metrics.apiCalls.shift();
        }
        
        // Log slow API calls
        if (callTime > 1000) {
            console.warn(`Slow API call detected: ${url} took ${callTime}ms`);
        }
    }

    /**
     * Record graph rendering time
     */
    recordRenderTime(renderType, startTime, endTime, elementCount = null) {
        const renderTime = endTime - startTime;
        
        const renderMetric = {
            type: renderType,
            duration: renderTime,
            elementCount,
            elementsPerSecond: elementCount ? elementCount / (renderTime / 1000) : null,
            timestamp: Date.now()
        };
        
        this.metrics.renderTimes.push(renderMetric);
        
        // Keep only recent render times
        if (this.metrics.renderTimes.length > this.config.maxRenderTimeHistory) {
            this.metrics.renderTimes.shift();
        }
        
        // Log slow renders
        if (renderTime > 500) {
            console.warn(`Slow render detected: ${renderType} took ${renderTime}ms`);
        }
    }

    /**
     * Start memory monitoring
     */
    startMemoryMonitoring() {
        if (!window.performance || !window.performance.memory) {
            console.warn('Memory monitoring not available in this browser');
            return;
        }
        
        const checkMemory = () => {
            if (!this.isMonitoring) return;
            
            const memory = window.performance.memory;
            const memoryInfo = {
                used: memory.usedJSHeapSize,
                total: memory.totalJSHeapSize,
                limit: memory.jsHeapSizeLimit,
                percentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
                timestamp: Date.now()
            };
            
            this.metrics.memoryUsage.push(memoryInfo);
            
            // Keep only recent memory measurements
            if (this.metrics.memoryUsage.length > 100) {
                this.metrics.memoryUsage.shift();
            }
            
            // Warning for high memory usage
            if (memoryInfo.percentage > 80) {
                console.warn(`High memory usage detected: ${memoryInfo.percentage.toFixed(1)}%`);
            }
            
            this.notifyObservers('memory', memoryInfo);
            
            setTimeout(checkMemory, this.config.memoryCheckInterval);
        };
        
        checkMemory();
    }

    /**
     * Monitor user interactions
     */
    monitorUserInteractions() {
        const interactionTypes = ['click', 'keydown', 'scroll', 'resize'];
        
        interactionTypes.forEach(eventType => {
            document.addEventListener(eventType, (event) => {
                if (!this.isMonitoring) return;
                
                const interaction = {
                    type: eventType,
                    target: event.target.tagName || 'unknown',
                    timestamp: Date.now()
                };
                
                this.metrics.userInteractions.push(interaction);
                
                // Keep only recent interactions
                if (this.metrics.userInteractions.length > 1000) {
                    this.metrics.userInteractions.shift();
                }
            }, { passive: true });
        });
    }

    /**
     * Monitor API calls by intercepting fetch
     */
    monitorApiCalls() {
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = async function(...args) {
            if (!self.isMonitoring) {
                return originalFetch.apply(this, args);
            }
            
            const startTime = performance.now();
            const url = args[0];
            const options = args[1] || {};
            const method = options.method || 'GET';
            
            try {
                const response = await originalFetch.apply(this, args);
                const endTime = performance.now();
                
                // Try to get response size
                let responseSize = null;
                const contentLength = response.headers.get('content-length');
                if (contentLength) {
                    responseSize = parseInt(contentLength);
                }
                
                self.recordApiCall(url, method, startTime, endTime, response.ok, responseSize);
                
                return response;
            } catch (error) {
                const endTime = performance.now();
                self.recordApiCall(url, method, startTime, endTime, false);
                throw error;
            }
        };
    }

    /**
     * Start periodic performance reporting
     */
    startPeriodicReporting() {
        const report = () => {
            if (!this.isMonitoring) return;
            
            const summary = this.generatePerformanceSummary();
            console.log('Performance Summary:', summary);
            
            setTimeout(report, this.config.performanceReportInterval);
        };
        
        setTimeout(report, this.config.performanceReportInterval);
    }

    /**
     * Generate performance summary
     */
    generatePerformanceSummary() {
        const now = Date.now();
        const recentWindow = 60000; // Last 60 seconds
        
        // Recent API calls
        const recentApiCalls = this.metrics.apiCalls.filter(
            call => now - call.timestamp < recentWindow
        );
        
        // Recent render times
        const recentRenders = this.metrics.renderTimes.filter(
            render => now - render.timestamp < recentWindow
        );
        
        // Memory usage
        const currentMemory = this.metrics.memoryUsage.length > 0 
            ? this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1]
            : null;
        
        return {
            uptime: now - this.startTime,
            pageLoad: this.metrics.pageLoad,
            graphLoad: this.metrics.graphLoad,
            recentApiCalls: {
                count: recentApiCalls.length,
                averageTime: recentApiCalls.length > 0 
                    ? recentApiCalls.reduce((sum, call) => sum + call.duration, 0) / recentApiCalls.length
                    : 0,
                successRate: recentApiCalls.length > 0
                    ? (recentApiCalls.filter(call => call.success).length / recentApiCalls.length) * 100
                    : 100
            },
            recentRenders: {
                count: recentRenders.length,
                averageTime: recentRenders.length > 0
                    ? recentRenders.reduce((sum, render) => sum + render.duration, 0) / recentRenders.length
                    : 0
            },
            memory: currentMemory,
            userInteractionRate: this.getUserInteractionRate()
        };
    }

    /**
     * Get user interaction rate
     */
    getUserInteractionRate() {
        const now = Date.now();
        const window = 60000; // Last 60 seconds
        
        const recentInteractions = this.metrics.userInteractions.filter(
            interaction => now - interaction.timestamp < window
        );
        
        return recentInteractions.length / (window / 1000); // Interactions per second
    }

    /**
     * Get browser capabilities
     */
    getBrowserCapabilities() {
        return {
            webgl: this.supportsWebGL(),
            webgl2: this.supportsWebGL2(),
            canvas: this.supportsCanvas(),
            svg: this.supportsSVG(),
            performanceApi: !!window.performance,
            memoryApi: !!(window.performance && window.performance.memory),
            intersectionObserver: !!window.IntersectionObserver,
            requestIdleCallback: !!window.requestIdleCallback,
            devicePixelRatio: window.devicePixelRatio || 1,
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            maxTouchPoints: navigator.maxTouchPoints || 0
        };
    }

    /**
     * Check WebGL support
     */
    supportsWebGL() {
        try {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
        } catch (e) {
            return false;
        }
    }

    /**
     * Check WebGL2 support
     */
    supportsWebGL2() {
        try {
            const canvas = document.createElement('canvas');
            return !!canvas.getContext('webgl2');
        } catch (e) {
            return false;
        }
    }

    /**
     * Check Canvas support
     */
    supportsCanvas() {
        try {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext && canvas.getContext('2d'));
        } catch (e) {
            return false;
        }
    }

    /**
     * Check SVG support
     */
    supportsSVG() {
        return !!(document.createElementNS && document.createElementNS('http://www.w3.org/2000/svg', 'svg').createSVGRect);
    }

    /**
     * Add performance observer
     */
    addObserver(type, callback) {
        if (this.observers[type]) {
            this.observers[type].push(callback);
        }
    }

    /**
     * Remove performance observer
     */
    removeObserver(type, callback) {
        if (this.observers[type]) {
            const index = this.observers[type].indexOf(callback);
            if (index > -1) {
                this.observers[type].splice(index, 1);
            }
        }
    }

    /**
     * Notify observers
     */
    notifyObservers(type, data) {
        if (this.observers[type]) {
            this.observers[type].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${type} observer:`, error);
                }
            });
        }
    }

    /**
     * Export performance data
     */
    exportData() {
        return {
            metrics: this.metrics,
            summary: this.generatePerformanceSummary(),
            browserCapabilities: this.getBrowserCapabilities(),
            timestamp: Date.now()
        };
    }

    /**
     * Clear performance data
     */
    clearData() {
        this.metrics = {
            pageLoad: null,
            graphLoad: null,
            apiCalls: [],
            renderTimes: [],
            memoryUsage: [],
            userInteractions: []
        };
        console.log('Performance data cleared');
    }
}

// Export for use in other modules
window.PerformanceMonitor = PerformanceMonitor;