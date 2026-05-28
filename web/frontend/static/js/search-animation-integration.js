/**
 * Search Animation Integration
 * 
 * This script integrates the SearchAnimation component with the existing
 * search functionality in app.js.
 * 
 * Uses Server-Sent Events (SSE) for real-time phase updates from backend.
 * Falls back to client-side estimation if SSE is not available.
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if SearchAnimation class exists
    if (typeof SearchAnimation === 'undefined') {
        console.error('SearchAnimation class not loaded. Check that search-animation.js is loaded before this script.');
        return;
    }

    // Initialize SearchAnimation
    let searchAnimation = null;
    let currentEventSource = null;
    let currentSearchId = null;
    
    try {
        const container = document.getElementById('search-animation');
        if (container) {
            searchAnimation = new SearchAnimation('#search-animation', {
                animationStyle: 'chasing-dots',
                showProgressBar: true,
                showIcon: false,
                sseEndpoint: '/api/v1/search/phases'
            });
            
            console.log('\u2713 SearchAnimation initialized');
        } else {
            console.warn('SearchAnimation container not found');
            return;
        }
    } catch (error) {
        console.error('Failed to initialize SearchAnimation:', error);
        return;
    }

    // Function to close existing SSE connection
    function closeSSEConnection() {
        if (currentEventSource) {
            currentEventSource.close();
            currentEventSource = null;
        }
        currentSearchId = null;
    }

    // Function to connect to SSE for a specific search
    function connectToSSE(searchId) {
        // Close any existing connection
        closeSSEConnection();
        
        if (!searchAnimation || !searchId) return null;
        
        currentSearchId = searchId;
        const sseUrl = `/api/v1/search/phases?search_id=${encodeURIComponent(searchId)}`;
        
        try {
            console.log(`\u2713 Connecting to SSE: ${sseUrl}`);
            currentEventSource = new EventSource(sseUrl);
            
            currentEventSource.onopen = function() {
                console.log(`\u2713 SSE connection opened for search: ${searchId}`);
                // Once SSE is connected, stop client-side estimation
                if (searchAnimation && searchAnimation.stopClientSideProgression) {
                    searchAnimation.stopClientSideProgression();
                }
            };
            
            currentEventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    console.log('SSE message:', data);
                    
                    if (!searchAnimation) return;
                    
                    if (data.phase) {
                        searchAnimation.nextPhase(data.phase);
                    }
                    if (data.progress !== undefined) {
                        searchAnimation.setProgress(data.progress);
                    }
                    if (data.error) {
                        searchAnimation.error(data.error_message || data.error);
                    }
                    if (data.complete) {
                        searchAnimation.complete();
                        // Auto-hide animation after showing completion
                        setTimeout(() => {
                            const container = document.getElementById('search-animation');
                            if (container) container.style.display = 'none';
                        }, 1000);
                    }
                } catch (error) {
                    console.error('Error parsing SSE message:', error);
                }
            };
            
            currentEventSource.onerror = function(error) {
                console.warn('\u26A0 SSE connection closed (stream ended):', error);
                // This is normal - stream ends when search completes
            };
            
            return currentEventSource;
            
        } catch (error) {
            console.warn('\u26A0 SSE not supported, using client-side estimation:', error);
            if (searchAnimation && searchAnimation.connectSSE) {
                searchAnimation.connectSSE(); // Fallback to client-side
            }
            return null;
        }
    }

    // Override loading functions if SearchAnimation is available
    if (searchAnimation) {
        // Save original functions
        const originalShowLoading = window.showLoading;
        const originalHideLoading = window.hideLoading;
        const originalShowError = window.showError;

        // Override showLoading
        window.showLoading = function() {
            const animationContainer = document.getElementById('search-animation');
            if (animationContainer) {
                animationContainer.style.display = 'flex';
            }
            
            if (searchAnimation) {
                searchAnimation.reset();
                searchAnimation.start();
                // Start with client-side estimation initially (no search_id yet)
                // Don't call searchAnimation.connectSSE() - that uses default URL
                // We'll connect to SSE with the actual search_id when we get it from the response
            }
            
            // Hide old loading indicator
            const oldLoading = document.getElementById('loading-indicator');
            const oldError = document.getElementById('error-message');
            if (oldLoading) oldLoading.style.display = 'none';
            if (oldError) oldError.style.display = 'none';
            
            // Call original if it exists
            if (originalShowLoading) originalShowLoading();
        };

        // Override hideLoading
        window.hideLoading = function() {
            // Close SSE connection
            closeSSEConnection();
            
            // Hide old loading indicator
            const oldLoading = document.getElementById('loading-indicator');
            if (oldLoading) oldLoading.style.display = 'none';
            
            // Call original if it exists
            if (originalHideLoading) originalHideLoading();
        };

        // Override showError
        window.showError = function(message) {
            if (searchAnimation) {
                searchAnimation.error(message);
            }
            
            // Close SSE connection on error
            closeSSEConnection();
            
            // Hide animation after error is shown
            const animationContainer = document.getElementById('search-animation');
            if (animationContainer) {
                setTimeout(() => {
                    animationContainer.style.display = 'none';
                }, 2000);
            }
            
            // Fallback to old error message
            const oldError = document.getElementById('error-message');
            if (oldError) {
                oldError.textContent = message;
                oldError.style.display = 'block';
                
                // Hide after 5 seconds
                setTimeout(() => {
                    if (oldError) oldError.style.display = 'none';
                }, 5000);
            }
            
            // Call original if it exists
            if (originalShowError) originalShowError(message);
        };

        // Patch fetch to intercept search responses and extract search_id
        if (window.fetch) {
            const originalFetch = window.fetch;
            window.fetch = async function(url, options) {
                // If this is a search request (and not SSE)
                if (typeof url === 'string' && url.includes('/api/v1/search') && !url.includes('/phases')) {
                    const response = await originalFetch.call(this, url, options);
                    
                    // If response is OK, try to extract search_id
                    if (response.ok) {
                        try {
                            const data = await response.clone().json();
                            const searchId = data?.search_id || data?.searchId;
                            if (searchId && searchAnimation) {
                                console.log(`\u2713 Extracted search_id: ${searchId}, connecting to SSE`);
                                // Stop client-side estimation
                                if (searchAnimation.stopClientSideProgression) {
                                    searchAnimation.stopClientSideProgression();
                                }
                                // Connect to SSE with the backend's search_id
                                connectToSSE(searchId);
                            }
                        } catch (error) {
                            console.warn('Could not extract search_id from response:', error);
                        }
                    }
                    
                    return response;
                }
                
                return originalFetch.call(this, url, options);
            };
        }

        console.log('\u2713 SearchAnimation integration complete');
    }
});
