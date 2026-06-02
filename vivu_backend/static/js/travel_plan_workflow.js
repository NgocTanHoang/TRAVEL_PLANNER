/**
 * Travel Plan Workflow - 4 Steps
 * Handles the entire workflow for creating travel plans
 */

// Global state
const workflowState = {
    currentStep: 1,
    step1Data: null,
    step2Data: null,
    step3Data: null,
    step4Data: null,
    activeStream: null,
    authRedirectPending: false,
    postStreamReconnectTimer: null,
    streamedDayKeys: new Set(),
    streamedProgressKeys: new Set()
};

const ACTIVE_TRAVEL_STREAM_STORAGE_KEY = 'vivu-active-travel-stream';
const AUTH_REQUIRED_MESSAGE = 'Vui lòng đăng nhập để sử dụng tính năng này.';
const STREAM_FAILURE_MESSAGE = 'Hệ thống AI gặp sự cố. Vui lòng thử lại.';
const LOGIN_PATH = '/accounts/login/';
const nativeFetch = window.fetch.bind(window);
let pendingModalAction = null;

window.fetch = async function(input, init = {}) {
    const response = await nativeFetch(input, init);
    const requestUrl = typeof input === 'string' ? input : input?.url || '';
    const skipAuthHandling = Boolean(init?.__skipAuthHandling);

    if (!skipAuthHandling && (response.status === 401 || response.status === 403) && requestUrl.includes('/api/')) {
        handleProtectedRouteFailure();
    }

    return response;
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWorkflow();
    loadTravelStyles(); // Load travel styles from API
    resumeTravelPlanStreamFromStorage();
});

function initializeWorkflow() {
    // Setup autocomplete for inputs
    setupAutocomplete('origin-input', 'origin-autocomplete');
    setupAutocomplete('destination-input', 'destination-autocomplete');
    
    // Setup location button
    const locationBtn = document.getElementById('use-current-location-btn');
    if (locationBtn) {
        locationBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleCurrentLocation();
        });
    }
    
    // Setup chip buttons
    const editAddressBtn = document.getElementById('edit-address-btn');
    const confirmAddressBtn = document.getElementById('confirm-address-btn');
    
    if (editAddressBtn) {
        editAddressBtn.addEventListener('click', function() {
            const chip = document.getElementById('detected-chip');
            const miniMap = document.getElementById('origin-mini-map');
            if (chip) chip.classList.add('hidden');
            if (miniMap) miniMap.classList.add('hidden');
            const originInput = document.getElementById('origin-input');
            if (originInput) {
                originInput.focus();
                originInput.value = '';
            }
            const statusSpan = document.getElementById('location-status');
            if (statusSpan) statusSpan.textContent = '';
        });
    }
    
    if (confirmAddressBtn) {
        confirmAddressBtn.addEventListener('click', function() {
            const originInput = document.getElementById('origin-input');
            const addressSpan = document.getElementById('detected-address');
            const statusSpan = document.getElementById('location-status');
            
            // Fill the input with detected address
            if (addressSpan && originInput) {
                // Remove accuracy text for input value
                const addressText = addressSpan.textContent.split(' • ')[0];
                originInput.value = addressText;
            }
            
            if (statusSpan) {
                statusSpan.textContent = '✓ Vị trí đã được xác nhận';
                statusSpan.style.color = 'var(--color-accent-dark)';
            }
            
            // Optionally focus next field
            const destinationInput = document.getElementById('destination-input');
            if (destinationInput) destinationInput.focus();
        });
    }
    
    // Setup form submissions
    const step1Form = document.getElementById('step1-form');
    if (step1Form) {
        step1Form.addEventListener('submit', handleStep1Submit);
    }
    
    const step2Form = document.getElementById('step2-form');
    if (step2Form) {
        step2Form.addEventListener('submit', handleStep2Submit);
        
        // Initialize Flatpickr for start-date (no limit)
        const startDateInput = document.getElementById('start-date');
        let startDatePicker = null;
        
        if (startDateInput) {
            startDatePicker = flatpickr(startDateInput, {
                dateFormat: "d/m/Y",
                minDate: "today",
                locale: "vn", // Vietnamese locale
                defaultDate: null // No default date
            });
        }
    }
    
    // Days input - limit to 14 days
    const daysInput = document.getElementById('days');
    if (daysInput) {
        daysInput.addEventListener('change', function(e) {
            const days = parseInt(this.value);
            if (days < 1) {
                showErrorModal('Số ngày phải lớn hơn 0');
                this.value = 1;
                e.preventDefault();
                e.stopPropagation();
            } else if (days > 14) {
                showErrorModal('Số ngày không được vượt quá 14 ngày');
                this.value = 14;
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        // Also validate on blur to catch paste events
        daysInput.addEventListener('blur', function(e) {
            const days = parseInt(this.value);
            if (days < 1) {
                showErrorModal('Số ngày phải lớn hơn 0');
                this.value = 1;
                e.preventDefault();
                e.stopPropagation();
            } else if (days > 14) {
                showErrorModal('Số ngày không được vượt quá 14 ngày');
                this.value = 14;
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }
    
    // Travelers input - limit to 20 (1 family)
    const travelersInput = document.getElementById('travelers');
    if (travelersInput) {
        travelersInput.addEventListener('change', function(e) {
            const travelers = parseInt(this.value);
            if (travelers < 1) {
                showErrorModal('Số người phải lớn hơn 0');
                this.value = 1;
                e.preventDefault();
                e.stopPropagation();
            } else if (travelers > 20) {
                showErrorModal('Số người không được vượt quá 20 người (tương ứng với 1 gia đình)');
                this.value = 20;
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        // Also validate on blur to catch paste events
        travelersInput.addEventListener('blur', function(e) {
            const travelers = parseInt(this.value);
            if (travelers < 1) {
                showErrorModal('Số người phải lớn hơn 0');
                this.value = 1;
                e.preventDefault();
                e.stopPropagation();
            } else if (travelers > 20) {
                showErrorModal('Số người không được vượt quá 20 người (tương ứng với 1 gia đình)');
                this.value = 20;
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }
}

// Autocomplete setup
function setupAutocomplete(inputId, dropdownId) {
    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    
    if (!input || !dropdown) return;
    
    let debounceTimer;
    
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 2) {
            dropdown.classList.remove('show');
            return;
        }
        
        debounceTimer = setTimeout(() => {
            fetchSuggestions(query, dropdown);
        }, 300);
    });
    
    input.addEventListener('focus', function() {
        if (dropdown.children.length > 0) {
            dropdown.classList.add('show');
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        // If click is outside input and dropdown, close dropdown
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Close dropdown when clicking on map or map controls
    // This prevents dropdown from blocking map interactions
    setTimeout(() => {
        const miniMap = document.getElementById('origin-mini-map');
        if (miniMap && !miniMap.classList.contains('hidden')) {
            // Close when clicking on map container (but not on controls directly)
            miniMap.addEventListener('mousedown', function(e) {
                // Only close if clicking on the map itself, not on controls
                if (e.target.classList.contains('leaflet-container') || 
                    e.target.closest('.leaflet-pane')) {
                    dropdown.classList.remove('show');
                }
            }, { once: false });
        }
    }, 500);
}

async function fetchSuggestions(query, dropdown) {
    try {
        const response = await fetch(`/api/v1/locations/suggestions/?q=${encodeURIComponent(query)}&type=both&limit=10`);
        const data = await response.json();
        
        dropdown.innerHTML = '';
        
        if (data.suggestions && data.suggestions.length > 0) {
            data.suggestions.forEach(suggestion => {
                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                item.textContent = suggestion;
                item.addEventListener('click', function() {
                    const input = dropdown.previousElementSibling;
                    if (input && input.tagName === 'INPUT') {
                        input.value = suggestion;
                    } else {
                        // Handle location button case
                        const container = dropdown.parentElement;
                        const input = container.querySelector('input');
                        if (input) input.value = suggestion;
                    }
                    dropdown.classList.remove('show');
                });
                dropdown.appendChild(item);
            });
            dropdown.classList.add('show');
        }
    } catch (error) {
        console.error('Error fetching suggestions:', error);
    }
}

// Mini map instance
let originMap = null;
let originMarker = null;
let originAccuracyCircle = null;
let destinationMarker = null;
let routePreviewLine = null;
let sovereigntyMarkersAdded = false;
let isUpdatingMapViewport = false;
let isResolvingCurrentLocation = false;

const CARTO_DARK_TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const VIETNAM_MAP_BOUNDS = L.latLngBounds(
    [6.0, 102.0],
    [24.0, 118.0]
);
const VIETNAM_MIN_ZOOM = 5;
const VIETNAM_DEFAULT_CENTER = [16.2, 106.2];
const VIETNAM_DEFAULT_ZOOM = 5;
const SOVEREIGNTY_MARKERS = [
    {
        coords: [16.5, 112.0],
        text: 'Quần đảo Hoàng Sa <br>(Thành phố Đà Nẵng, Việt Nam)'
    },
    {
        coords: [10.0, 114.3],
        text: 'Quần đảo Trường Sa <br>(Tỉnh Khánh Hòa, Việt Nam)'
    }
];

function addSovereigntyMarkers(mapInstance) {
    if (!mapInstance || sovereigntyMarkersAdded) return;

    SOVEREIGNTY_MARKERS.forEach((item) => {
        L.marker(item.coords, {
            interactive: false,
            keyboard: false,
            zIndexOffset: 1000,
            icon: L.divIcon({
                className: 'sovereignty-marker',
                html: `
                    <div class="sovereignty-label">
                        <span class="sovereignty-label__flag">🇻🇳</span>
                        <span>${item.text}</span>
                    </div>
                `,
                iconSize: [216, 48],
                iconAnchor: [108, 24]
            })
        }).addTo(mapInstance);
    });

    sovereigntyMarkersAdded = true;
}

function createRouteMarkerIcon(type, label = '') {
    const palette = type === 'destination'
        ? {
            wrapper: 'travel-route-anchor travel-route-anchor--destination',
            dot: 'travel-route-dot travel-route-dot--destination'
        }
        : {
            wrapper: 'travel-route-anchor travel-route-anchor--origin',
            dot: 'travel-route-dot travel-route-dot--origin'
        };

    const safeLabel = (label || (type === 'destination' ? 'Điểm đến' : 'Điểm đi của bạn'))
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    return L.divIcon({
        className: 'travel-route-marker',
        html: `
            <span class="${palette.wrapper}">
                <span class="${palette.dot}"></span>
                <span>${safeLabel}</span>
            </span>
        `,
        iconSize: [150, 34],
        iconAnchor: type === 'destination' ? [20, 17] : [130, 17],
        popupAnchor: [0, -18]
    });
}

function ensureOriginMap(center = VIETNAM_DEFAULT_CENTER, zoom = VIETNAM_DEFAULT_ZOOM) {
    const miniMap = document.getElementById('origin-mini-map');
    if (!miniMap) return null;

    miniMap.classList.remove('hidden');
    miniMap.classList.add('visible');
    miniMap.setAttribute('aria-hidden', 'false');

    if (!originMap) {
        originMap = L.map('origin-mini-map', {
            zoomControl: true,
            scrollWheelZoom: true,
            doubleClickZoom: true,
            touchZoom: true,
            boxZoom: false,
            dragging: true,
            minZoom: VIETNAM_MIN_ZOOM,
            maxZoom: 16,
            maxBounds: VIETNAM_MAP_BOUNDS,
            maxBoundsViscosity: 1.0
        }).setView(center, zoom);

        L.tileLayer(CARTO_DARK_TILE_URL, {
            attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap contributors',
            minZoom: VIETNAM_MIN_ZOOM,
            maxZoom: 16,
            noWrap: true
        }).addTo(originMap);

        addSovereigntyMarkers(originMap);
    }

    setTimeout(() => {
        if (originMap) {
            originMap.invalidateSize();
        }
    }, 100);

    return originMap;
}

function resetRoutePreviewLayers() {
    if (!originMap) return;

    if (routePreviewLine) {
        originMap.removeLayer(routePreviewLine);
        routePreviewLine = null;
    }

    if (destinationMarker) {
        originMap.removeLayer(destinationMarker);
        destinationMarker = null;
    }
}

function setMapViewportSafely(map, callback) {
    if (!map || typeof callback !== 'function') return;
    if (isUpdatingMapViewport) return;

    isUpdatingMapViewport = true;
    try {
        callback();
    } finally {
        window.setTimeout(() => {
            isUpdatingMapViewport = false;
        }, 0);
    }
}

function updateOriginMap(lat, lon, options = {}) {
    const {
        accuracy = 0,
        originLabel = 'Điểm đi hiện tại',
        destination = null
    } = options;

    const map = ensureOriginMap([lat, lon], accuracy > 100 ? 13 : 15);
    if (!map) return;

    if (!originMarker) {
        originMarker = L.marker([lat, lon], {
            icon: createRouteMarkerIcon('origin', originLabel)
        }).addTo(map);
    } else {
        originMarker.setLatLng([lat, lon]);
        originMarker.setIcon(createRouteMarkerIcon('origin', originLabel));
    }
    originMarker.bindPopup(originLabel);

    if (originAccuracyCircle) {
        map.removeLayer(originAccuracyCircle);
        originAccuracyCircle = null;
    }

    if (accuracy > 0) {
        originAccuracyCircle = L.circle([lat, lon], {
            radius: accuracy,
            color: '#0f766e',
            fillColor: '#14b8a6',
            fillOpacity: 0.12,
            weight: 2
        }).addTo(map);
    }

    resetRoutePreviewLayers();

    if (destination && Number.isFinite(destination.lat) && Number.isFinite(destination.lon)) {
        destinationMarker = L.marker([destination.lat, destination.lon], {
            icon: createRouteMarkerIcon('destination', destination.label || 'Điểm đến')
        }).addTo(map);
        destinationMarker.bindPopup(destination.label || 'Điểm đến');

        routePreviewLine = L.polyline([
            [lat, lon],
            [destination.lat, destination.lon]
        ], {
            color: '#34d399',
            weight: 4,
            opacity: 0.8,
            lineCap: 'round',
            dashArray: '10, 10',
            className: 'animated-route-line'
        }).addTo(map);

        const routeBounds = L.latLngBounds([
            [lat, lon],
            [destination.lat, destination.lon]
        ]);
        setMapViewportSafely(map, () => {
            map.fitBounds(routeBounds.pad(0.2), {
                padding: [28, 28],
                maxZoom: 12,
                animate: false
            });
            map.panInsideBounds(VIETNAM_MAP_BOUNDS, { animate: false });
        });
    } else {
        setMapViewportSafely(map, () => {
            map.setView([lat, lon], accuracy > 100 ? 13 : 15, {
                animate: false
            });
        });
    }
}

function updateRoutePreviewMap(data) {
    if (!data || !data.origin || !data.destination) return;

    const originInput = document.getElementById('origin-input');
    const rawOriginLat = originInput?.dataset.lat;
    const rawOriginLon = originInput?.dataset.lon;
    const preferredOriginLat = rawOriginLat !== undefined && rawOriginLat !== '' ? Number(rawOriginLat) : NaN;
    const preferredOriginLon = rawOriginLon !== undefined && rawOriginLon !== '' ? Number(rawOriginLon) : NaN;

    const originLat = Number.isFinite(preferredOriginLat) ? preferredOriginLat : Number(data.origin.latitude);
    const originLon = Number.isFinite(preferredOriginLon) ? preferredOriginLon : Number(data.origin.longitude);
    const destinationLat = Number(data.destination.latitude);
    const destinationLon = Number(data.destination.longitude);

    if (!Number.isFinite(originLat) || !Number.isFinite(originLon) || !Number.isFinite(destinationLat) || !Number.isFinite(destinationLon)) {
        return;
    }

    updateOriginMap(originLat, originLon, {
        accuracy: 0,
        originLabel: data.origin.name || 'Điểm đi',
        destination: {
            lat: destinationLat,
            lon: destinationLon,
            label: data.destination.name || 'Điểm đến'
        }
    });
}

// Step 1: Location Selection
async function handleStep1Submit(e) {
    e.preventDefault();
    
    const originInput = document.getElementById('origin-input');
    const destinationInput = document.getElementById('destination-input');
    
    const origin = originInput ? originInput.value.trim() : '';
    const destination = destinationInput ? destinationInput.value.trim() : '';
    
    // Validation
    if (!origin || origin.length < 2) {
        showError('Vui lòng nhập điểm xuất phát (ít nhất 2 ký tự)');
        if (originInput) originInput.focus();
        return;
    }
    
    if (!destination || destination.length < 2) {
        showError('Vui lòng nhập điểm đến (ít nhất 2 ký tự)');
        if (destinationInput) destinationInput.focus();
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    const resultDiv = document.getElementById('step1-result');
    
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Đang kiểm tra...';
    
    // Clear previous errors
    if (resultDiv) {
        resultDiv.innerHTML = '';
        resultDiv.style.display = 'none';
    }
    
    try {
        console.log('Sending Step 1 request:', { origin, destination });
        
        const response = await fetch('/api/v1/travel-plans/step1/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                origin: origin,
                destination: destination
            })
        });
        
        console.log('Step 1 response status:', response.status);
        const data = await response.json();
        console.log('Step 1 response data:', data);
        
        if (response.ok && data.status === 'success') {
            workflowState.step1Data = data;
            displayStep1Result(data);
            setTimeout(() => {
                goToStep(2);
            }, 1000);
        } else {
            // Show detailed error message
            const errorMsg = data.error || 'Không thể xử lý yêu cầu';
            showError(errorMsg);
            
            // Highlight problematic input
            if (data.origin && !data.destination) {
                if (destinationInput) destinationInput.style.borderColor = '#dc2626';
            } else if (data.destination && !data.origin) {
                if (originInput) originInput.style.borderColor = '#dc2626';
            } else {
                if (originInput) originInput.style.borderColor = '#dc2626';
                if (destinationInput) destinationInput.style.borderColor = '#dc2626';
            }
        }
    } catch (error) {
        console.error('Step 1 error:', error);
        showError('Lỗi kết nối. Vui lòng kiểm tra kết nối mạng và thử lại.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

function showError(message) {
    const resultDiv = document.getElementById('step1-result');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <div style="background: #fee2e2; border: 2px solid #dc2626; border-radius: 12px; padding: 1rem; margin-top: 1rem; color: #991b1b;">
                <strong>⚠️ Lỗi:</strong> ${message}
                <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                    <strong>Gợi ý:</strong>
                    <ul style="margin: 0.5rem 0 0 1.5rem; padding: 0;">
                        <li>Sử dụng tên tỉnh/thành phố đầy đủ (ví dụ: "Thành phố Hồ Chí Minh", "Thành phố Hà Nội")</li>
                        <li>Hoặc sử dụng autocomplete để chọn từ danh sách gợi ý</li>
                        <li>Kiểm tra chính tả và dấu tiếng Việt</li>
                    </ul>
                </div>
            </div>
        `;
        resultDiv.style.display = 'block';
    } else {
        showErrorModal(message);
    }
}

// Error Modal Functions
function showErrorModal(message, type = 'error') {
    const overlay = document.getElementById('error-modal-overlay');
    const messageDiv = document.getElementById('error-modal-message');
    const header = overlay.querySelector('.error-modal-header');
    const icon = header.querySelector('.error-icon');
    
    if (!overlay || !messageDiv) return;
    
    // Update message
    messageDiv.textContent = message;
    
    // Update style based on type
    if (type === 'success') {
        header.classList.remove('error');
        header.classList.add('success');
        icon.textContent = '✓';
    } else {
        header.classList.remove('success');
        header.classList.add('error');
        icon.textContent = '⚠️';
    }
    
    // Show modal
    overlay.classList.add('show');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

function closeErrorModal(event) {
    // If event is provided and click is on overlay (not modal), close
    if (event && event.target.classList.contains('error-modal-overlay')) {
        const overlay = document.getElementById('error-modal-overlay');
        if (overlay) {
            overlay.classList.remove('show');
            document.body.style.overflow = '';
        }
    } else {
        // Close normally
        const overlay = document.getElementById('error-modal-overlay');
        if (overlay) {
            overlay.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeErrorModal();
    }
});

function showErrorModal(message, type = 'error', options = {}) {
    const overlay = document.getElementById('error-modal-overlay');
    const messageDiv = document.getElementById('error-modal-message');
    if (!overlay || !messageDiv) return;

    const header = overlay.querySelector('.error-modal-header');
    const icon = header?.querySelector('.error-icon');
    pendingModalAction = typeof options.onClose === 'function' ? options.onClose : null;

    messageDiv.textContent = message;

    if (type === 'success') {
        header?.classList.remove('error');
        header?.classList.add('success');
        if (icon) icon.textContent = '✓';
    } else {
        header?.classList.remove('success');
        header?.classList.add('error');
        if (icon) icon.textContent = '⚠️';
    }

    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeErrorModal(event) {
    if (event && !event.target.classList.contains('error-modal-overlay')) {
        return;
    }

    const overlay = document.getElementById('error-modal-overlay');
    if (overlay) {
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (pendingModalAction) {
        const action = pendingModalAction;
        pendingModalAction = null;
        workflowState.authRedirectPending = false;
        action();
    }
}

// Final frontend overrides for streaming UX and reconnect behavior.
async function preflightTravelPlanStream(threadId) {
    const response = await fetch(`/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`, {
        method: 'GET',
        headers: { Accept: 'text/event-stream' }
    });

    if (!response.ok) {
        let errorPayload = {};
        try {
            errorPayload = await parseJsonResponse(response, 'Không thể khôi phục luồng AI.');
        } catch (error) {
            throw new Error(error.message || 'Không thể khôi phục luồng AI.');
        }
        throw new Error(errorPayload.error || 'Không thể khôi phục luồng AI.');
    }

    if (response.body?.cancel) {
        try {
            await response.body.cancel();
        } catch (error) {
            console.warn('Không thể đóng preflight stream phụ.', error);
        }
    }
}

function connectTravelPlanEventSource(threadId) {
    const streamUrl = `/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`;
    const eventSource = new EventSource(streamUrl);

    workflowState.activeStream = {
        ...(workflowState.activeStream || {}),
        threadId,
        eventSource,
        status: 'running'
    };

    ['connected', 'progress', 'day_ready', 'completed', 'error'].forEach((eventName) => {
        eventSource.addEventListener(eventName, (event) => {
            let payload = {};
            try {
                payload = event.data ? JSON.parse(event.data) : {};
            } catch (error) {
                console.error('Không thể parse SSE payload:', error, event.data);
            }
            handleStreamEvent(eventName, payload);
        });
    });

    eventSource.onerror = () => {
        if (!workflowState.activeStream || workflowState.activeStream.threadId !== threadId) {
            eventSource.close();
            return;
        }

        eventSource.close();
        workflowState.activeStream.eventSource = null;

        if (workflowState.activeStream.status === 'completed') {
            return;
        }

        appendStreamingProgress('reconnect', 'Luồng SSE bị gián đoạn, đang thử kết nối lại…');
        workflowState.postStreamReconnectTimer = window.setTimeout(() => {
            connectTravelPlanEventSource(threadId);
        }, 1200);
    };
}

function goToStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');

        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });

    workflowState.currentStep = step;

    if (step === 3 && !workflowState.step3Data) {
        loadStep3();
    } else if (step === 4 && !workflowState.step4Data && !workflowState.activeStream) {
        loadStep4();
    }
}

async function createFinalPlan() {
    const createBtn = document.getElementById('step4-create');
    const resultDiv = document.getElementById('step4-result');
    const payload = buildStep4GenerationPayload();

    if (!payload.origin || !payload.destination || !payload.start_date) {
        showErrorModal('Thiếu dữ liệu hành trình. Vui lòng kiểm tra lại 4 bước trước khi tạo lịch trình.');
        return;
    }

    if (workflowState.activeStream?.threadId) {
        showErrorModal('Luồng AI hiện tại vẫn đang chạy. Vui lòng chờ hoàn tất hoặc tải lại trang để khôi phục.');
        return;
    }

    const threadId = generateTravelPlanThreadId();
    const originalLabel = createBtn ? createBtn.innerHTML : '';

    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khởi tạo luồng AI...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(payload, threadId);
    }

    try {
        registerActiveStream(threadId, payload, 'live');
        appendStreamingProgress('bootstrap', 'Đã tạo thread_id, đang yêu cầu backend bắt đầu lập lịch trình…');
        await bootstrapTravelPlanStream(payload, threadId);
    } catch (error) {
        console.error('Create final plan stream error:', error);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = buildSafeFallbackStep4Data(payload, error.message || 'Không thể hoàn thiện lịch trình AI.');
        }
        displayStep4Result(workflowState.step4Data);
        showErrorModal(error.message || 'Không thể hoàn tất lịch trình lúc này. Vui lòng thử lại.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalLabel;
        }
    }
}

async function resumeTravelPlanStreamFromStorage() {
    const persisted = loadPersistedTravelStream();
    if (!persisted?.threadId || !persisted?.payload) return;

    hydrateWorkflowStateFromPayload(persisted.payload);
    workflowState.step4Data = workflowState.step4Data || { status: 'streaming' };
    goToStep(4);

    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(persisted.payload, persisted.threadId);
    }
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khôi phục luồng AI...';
    }

    registerActiveStream(persisted.threadId, persisted.payload, 'resume');
    appendStreamingProgress('resume', 'Đã tìm thấy thread_id trước đó, đang phát lại tiến độ…');

    try {
        await preflightTravelPlanStream(persisted.threadId);
    } catch (error) {
        cleanupActiveStream({ clearStorage: true, clearData: true });
        showErrorModal(error.message || 'Không thể khôi phục luồng AI.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lịch trình';
        }
        return;
    }

    connectTravelPlanEventSource(persisted.threadId);
}

window.goToStep = goToStep;
window.createFinalPlan = createFinalPlan;
window.closeErrorModal = closeErrorModal;

async function preflightTravelPlanStream(threadId) {
    const response = await fetch(`/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`, {
        method: 'GET',
        headers: {
            Accept: 'text/event-stream'
        }
    });

    if (!response.ok) {
        let errorPayload = {};
        try {
            errorPayload = await parseJsonResponse(response, 'Không thể khôi phục luồng AI.');
        } catch (error) {
            throw new Error(error.message || 'Không thể khôi phục luồng AI.');
        }
        throw new Error(errorPayload.error || 'Không thể khôi phục luồng AI.');
    }

    if (response.body?.cancel) {
        try {
            await response.body.cancel();
        } catch (error) {
            console.warn('Không thể đóng preflight stream phụ.', error);
        }
    }
}

function connectTravelPlanEventSource(threadId) {
    const streamUrl = `/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`;
    const eventSource = new EventSource(streamUrl);

    if (!workflowState.activeStream) {
        workflowState.activeStream = { threadId, eventSource, status: 'running' };
    } else {
        workflowState.activeStream.eventSource = eventSource;
        workflowState.activeStream.status = 'running';
    }

    ['connected', 'progress', 'day_ready', 'completed', 'error'].forEach((eventName) => {
        eventSource.addEventListener(eventName, (event) => {
            let payload = {};
            try {
                payload = event.data ? JSON.parse(event.data) : {};
            } catch (error) {
                console.error('Không thể parse SSE payload:', error, event.data);
            }
            handleStreamEvent(eventName, payload);
        });
    });

    eventSource.onerror = () => {
        if (!workflowState.activeStream || workflowState.activeStream.threadId !== threadId) {
            eventSource.close();
            return;
        }

        eventSource.close();
        workflowState.activeStream.eventSource = null;

        if (workflowState.activeStream.status === 'completed') {
            return;
        }

        appendStreamingProgress('reconnect', 'Luồng SSE bị gián đoạn, đang thử kết nối lại…');
        workflowState.postStreamReconnectTimer = window.setTimeout(() => {
            connectTravelPlanEventSource(threadId);
        }, 1200);
    };
}

function goToStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');

        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });

    workflowState.currentStep = step;

    if (step === 3 && !workflowState.step3Data) {
        loadStep3();
    } else if (step === 4 && !workflowState.step4Data && !workflowState.activeStream) {
        loadStep4();
    }
}

async function createFinalPlan() {
    const createBtn = document.getElementById('step4-create');
    const resultDiv = document.getElementById('step4-result');
    const payload = buildStep4GenerationPayload();

    if (!payload.origin || !payload.destination || !payload.start_date) {
        showErrorModal('Thiếu dữ liệu hành trình. Vui lòng kiểm tra lại 4 bước trước khi tạo lịch trình.');
        return;
    }

    if (workflowState.activeStream?.threadId) {
        showErrorModal('Luồng AI hiện tại vẫn đang chạy. Vui lòng chờ hoàn tất hoặc tải lại trang để khôi phục.');
        return;
    }

    const threadId = generateTravelPlanThreadId();
    const originalLabel = createBtn ? createBtn.innerHTML : '';

    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khởi tạo luồng AI...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(payload, threadId);
    }

    try {
        registerActiveStream(threadId, payload, 'live');
        appendStreamingProgress('bootstrap', 'Đã tạo thread_id, đang yêu cầu backend bắt đầu lập lịch trình…');
        await bootstrapTravelPlanStream(payload, threadId);
    } catch (error) {
        console.error('Create final plan stream error:', error);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = buildSafeFallbackStep4Data(
                payload,
                error.message || 'Không thể hoàn thiện lịch trình AI.'
            );
        }
        displayStep4Result(workflowState.step4Data);
        showErrorModal(error.message || 'Không thể hoàn tất lịch trình lúc này. Vui lòng thử lại.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalLabel;
        }
    }
}

async function resumeTravelPlanStreamFromStorage() {
    const persisted = loadPersistedTravelStream();
    if (!persisted?.threadId || !persisted?.payload) return;

    hydrateWorkflowStateFromPayload(persisted.payload);
    workflowState.step4Data = workflowState.step4Data || { status: 'streaming' };
    goToStep(4);

    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(persisted.payload, persisted.threadId);
    }
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khôi phục luồng AI...';
    }

    registerActiveStream(persisted.threadId, persisted.payload, 'resume');
    appendStreamingProgress('resume', 'Đã tìm thấy thread_id trước đó, đang phát lại tiến độ…');

    try {
        await preflightTravelPlanStream(persisted.threadId);
    } catch (error) {
        cleanupActiveStream({ clearStorage: true, clearData: true });
        showErrorModal(error.message || 'Không thể khôi phục luồng AI.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lịch trình';
        }
        return;
    }

    connectTravelPlanEventSource(persisted.threadId);
}

window.goToStep = goToStep;
window.createFinalPlan = createFinalPlan;
window.closeErrorModal = closeErrorModal;

function renderStreamingSkeletonDays(totalDays) {
    return Array.from({ length: totalDays }, (_, index) => `
        <article id="stream-day-skeleton-${index + 1}" class="timeline-day transition-all duration-300 ease-out opacity-80">
            <div class="timeline-day-header">
                <div>
                    <h4 class="text-base font-bold text-foreground">Ngày ${index + 1}</h4>
                    <div class="timeline-day-meta">
                        <span class="timeline-chip">Đang chờ AI hoàn thiện</span>
                    </div>
                </div>
                <span class="day-toggle-icon theme-text-muted">
                    <i class="fa-solid fa-hourglass-half"></i>
                </span>
            </div>
            <div class="timeline-day-body" style="display:block;">
                <div class="timeline-sections">
                    <div class="loading-line lg"></div>
                    <div class="loading-line md" style="margin-top:0.85rem;"></div>
                </div>
            </div>
        </article>
    `).join('');
}

function renderStep4StreamingShell(payload, threadId) {
    const totalDays = Math.max(1, Number(payload?.days || payload?.duration_days || 1));
    return `
        <div class="step4-shell">
            ${renderStepPanel({
                icon: 'fa-solid fa-tower-broadcast',
                title: 'Atlas đang phát lịch trình theo thời gian thực',
                subtitle: 'Luồng AI sẽ tự khôi phục nếu bạn tải lại trang trong lúc hệ thống còn giữ thread.',
                content: `
                    <div class="plan-overview-grid transition-all duration-300 ease-out">
                        <article class="plan-overview-card">
                            <span class="summary-label">Thread</span>
                            <span class="summary-value">${escapeHtml(threadId)}</span>
                        </article>
                        <article class="plan-overview-card">
                            <span class="summary-label">Tuyến hành trình</span>
                            <span class="summary-value">${escapeHtml(`${payload.origin || 'Điểm đi'} → ${payload.destination || 'Điểm đến'}`)}</span>
                        </article>
                        <article class="plan-overview-card">
                            <span class="summary-label">Trạng thái</span>
                            <span id="step4-stream-status" class="summary-value">Đang khởi tạo luồng AI…</span>
                        </article>
                    </div>
                    <div id="step4-stream-progress" class="timeline-list mt-5 transition-all duration-300 ease-out">
                        <div class="itinerary-activity">Đang chuẩn bị kết nối tới máy chủ phát trực tuyến…</div>
                    </div>
                `
            })}
            ${renderStepPanel({
                icon: 'fa-solid fa-calendar-days',
                title: 'Ngày đã hoàn thiện',
                subtitle: 'Mỗi thẻ sẽ thay thế skeleton ngay khi backend phát sự kiện day_ready.',
                content: `<div id="step4-stream-days" class="timeline-shell transition-all duration-300 ease-out">${renderStreamingSkeletonDays(totalDays)}</div>`
            })}
        </div>
    `;
}

function renderStreamingTimelineItem(item) {
    if (!item || typeof item !== 'object') {
        return '';
    }

    const time = escapeHtml(item.time || item.time_slot || '');
    const activityName = escapeHtml(item.activity_name || item.activity || 'Hoạt động');
    const note = escapeHtml(item.note || item.description || '');
    const placeName = escapeHtml(item.place_name || '');

    return `
        <article class="itinerary-activity transition-all duration-300 ease-out">
            ${time ? `<div class="timeline-chip">${time}</div>` : ''}
            <div class="mt-2 text-sm font-semibold text-foreground">${activityName}</div>
            ${placeName ? `<div class="budget-inline-meta">Địa điểm: ${placeName}</div>` : ''}
            ${note ? `<div class="budget-inline-meta">${note}</div>` : ''}
        </article>
    `;
}

function upsertStreamingDayCard(dayPayload) {
    const container = document.getElementById('step4-stream-days');
    if (!container || !dayPayload) return;

    const dayNumber = Number(dayPayload.day || 0) || 1;
    const cardId = `stream-day-card-${dayNumber}`;
    const skeleton = document.getElementById(`stream-day-skeleton-${dayNumber}`);
    const existing = document.getElementById(cardId);
    const timeline = Array.isArray(dayPayload.timeline) ? dayPayload.timeline : [];

    const markup = `
        <article id="${cardId}" class="timeline-day transition-all duration-300 ease-out">
            <div class="timeline-day-header">
                <div>
                    <h4 class="text-base font-bold text-foreground">📅 Ngày ${dayNumber}${dayPayload.date ? ` (${escapeHtml(dayPayload.date)})` : ''}${dayPayload.theme ? `: ${escapeHtml(dayPayload.theme)}` : ''}</h4>
                    <div class="timeline-day-meta">
                        <span class="timeline-chip"><i class="fa-regular fa-clock"></i> ${timeline.length} mốc hoạt động</span>
                        <span class="timeline-chip"><i class="fa-solid fa-check"></i> Đã sẵn sàng</span>
                    </div>
                </div>
            </div>
            <div class="timeline-day-body" style="display:block;">
                <div class="timeline-sections">
                    <section class="timeline-section">
                        <div class="timeline-section-title">
                            <i class="fa-solid fa-map-location-dot"></i>
                            <span>Lộ trình trong ngày</span>
                        </div>
                        <div class="timeline-list">
                            ${timeline.length ? timeline.map(renderStreamingTimelineItem).join('') : renderEmptyState('AI chưa gửi chi tiết timeline cho ngày này.')}
                        </div>
                    </section>
                </div>
            </div>
        </article>
    `;

    if (existing) {
        existing.outerHTML = markup;
    } else if (skeleton) {
        skeleton.outerHTML = markup;
    } else {
        container.insertAdjacentHTML('beforeend', markup);
    }
}

function appendStreamingProgress(step, message) {
    const progressContainer = document.getElementById('step4-stream-progress');
    const statusNode = document.getElementById('step4-stream-status');
    if (statusNode && message) {
        statusNode.textContent = message;
    }
    if (!progressContainer || !message) return;

    const progressKey = `${step || 'general'}:${message}`;
    if (workflowState.streamedProgressKeys.has(progressKey)) {
        return;
    }
    workflowState.streamedProgressKeys.add(progressKey);

    progressContainer.insertAdjacentHTML('beforeend', `
        <div class="itinerary-activity transition-all duration-300 ease-out">
            <strong class="block text-sm text-foreground">${escapeHtml(step || 'planning')}</strong>
            <span class="budget-inline-meta">${escapeHtml(message)}</span>
        </div>
    `);
}

function cleanupActiveStream({ clearStorage = true, clearData = false } = {}) {
    if (workflowState.activeStream?.eventSource) {
        workflowState.activeStream.eventSource.close();
    }

    if (workflowState.postStreamReconnectTimer) {
        window.clearTimeout(workflowState.postStreamReconnectTimer);
        workflowState.postStreamReconnectTimer = null;
    }

    workflowState.activeStream = null;
    resetStreamTrackingState();

    if (clearStorage) {
        clearPersistedTravelStream();
    }

    if (clearData) {
        workflowState.step4Data = null;
    }
}

function handleStreamEvent(eventType, payload) {
    if (!payload || typeof payload !== 'object') return;

    if (eventType === 'connected') {
        appendStreamingProgress('connected', payload.message || 'Đã kết nối tới luồng SSE.');
        return;
    }

    if (eventType === 'progress') {
        appendStreamingProgress(payload.step, payload.message || 'Đang xử lý lịch trình.');
        return;
    }

    if (eventType === 'day_ready') {
        upsertStreamingDayCard(payload);
        appendStreamingProgress('day_ready', `Đã hoàn thiện ngày ${payload.day}.`);
        return;
    }

    if (eventType === 'completed') {
        if (workflowState.activeStream) {
            workflowState.activeStream.status = 'completed';
        }
        workflowState.step4Data = payload.response || payload;
        displayStep4Result(workflowState.step4Data);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        showErrorModal('Lịch trình đã được tạo thành công.', 'success');
        const createBtn = document.getElementById('step4-create');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lại lịch trình';
        }
        return;
    }

    if (eventType === 'error') {
        appendStreamingProgress('error', payload.message || STREAM_FAILURE_MESSAGE);
        cleanupActiveStream({ clearStorage: false, clearData: false });
        showErrorModal(payload.message || STREAM_FAILURE_MESSAGE);
        const createBtn = document.getElementById('step4-create');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lịch trình';
        }
    }
}

function registerActiveStream(threadId, payload, mode = 'live') {
    workflowState.activeStream = {
        threadId,
        payload,
        mode,
        eventSource: null,
        status: 'running'
    };
    resetStreamTrackingState();
    persistActiveTravelStream({
        threadId,
        payload,
        mode,
        savedAt: new Date().toISOString()
    });
}

function connectTravelPlanEventSource(threadId) {
    const streamUrl = `/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`;
    const eventSource = new EventSource(streamUrl);

    if (!workflowState.activeStream) {
        workflowState.activeStream = { threadId, eventSource, status: 'running' };
    } else {
        workflowState.activeStream.eventSource = eventSource;
        workflowState.activeStream.status = 'running';
    }

    ['connected', 'progress', 'day_ready', 'completed', 'error'].forEach((eventName) => {
        eventSource.addEventListener(eventName, (event) => {
            let payload = {};
            try {
                payload = event.data ? JSON.parse(event.data) : {};
            } catch (error) {
                console.error('Không thể parse SSE payload:', error, event.data);
            }
            handleStreamEvent(eventName, payload);
        });
    });

    eventSource.onerror = () => {
        if (!workflowState.activeStream || workflowState.activeStream.threadId !== threadId) {
            eventSource.close();
            return;
        }

        eventSource.close();
        workflowState.activeStream.eventSource = null;

        if (workflowState.activeStream.status === 'completed') {
            return;
        }

        appendStreamingProgress('reconnect', 'Luồng SSE bị gián đoạn, đang thử kết nối lại…');
        workflowState.postStreamReconnectTimer = window.setTimeout(() => {
            connectTravelPlanEventSource(threadId);
        }, 1200);
    };
}

async function bootstrapTravelPlanStream(payload, threadId) {
    const response = await fetch('/api/v1/travel-plans/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            ...payload,
            thread_id: threadId
        })
    });

    if (!response.ok) {
        let errorPayload = {};
        try {
            errorPayload = await parseJsonResponse(response, 'Không thể khởi tạo luồng AI.');
        } catch (error) {
            throw new Error(error.message || 'Không thể khởi tạo luồng AI.');
        }
        throw new Error(errorPayload.error || 'Không thể khởi tạo luồng AI.');
    }

    if (response.body?.cancel) {
        try {
            await response.body.cancel();
        } catch (error) {
            console.warn('Không thể đóng bootstrap stream phụ.', error);
        }
    }

    connectTravelPlanEventSource(threadId);
}

async function preflightTravelPlanStream(threadId) {
    const response = await fetch(`/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`, {
        method: 'GET',
        headers: {
            Accept: 'text/event-stream'
        }
    });

    if (!response.ok) {
        let errorPayload = {};
        try {
            errorPayload = await parseJsonResponse(response, 'Không thể khôi phục luồng AI.');
        } catch (error) {
            throw new Error(error.message || 'Không thể khôi phục luồng AI.');
        }
        throw new Error(errorPayload.error || 'Không thể khôi phục luồng AI.');
    }

    if (response.body?.cancel) {
        try {
            await response.body.cancel();
        } catch (error) {
            console.warn('Không thể đóng preflight stream phụ.', error);
        }
    }
}

function goToStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');

        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });

    workflowState.currentStep = step;

    if (step === 3 && !workflowState.step3Data) {
        loadStep3();
    } else if (step === 4 && !workflowState.step4Data && !workflowState.activeStream) {
        loadStep4();
    }
}

async function createFinalPlan() {
    const createBtn = document.getElementById('step4-create');
    const resultDiv = document.getElementById('step4-result');
    const payload = buildStep4GenerationPayload();

    if (!payload.origin || !payload.destination || !payload.start_date) {
        showErrorModal('Thiếu dữ liệu hành trình. Vui lòng kiểm tra lại 4 bước trước khi tạo lịch trình.');
        return;
    }

    if (workflowState.activeStream?.threadId) {
        showErrorModal('Luồng AI hiện tại vẫn đang chạy. Vui lòng chờ hoàn tất hoặc tải lại trang để khôi phục.');
        return;
    }

    const threadId = generateTravelPlanThreadId();
    const originalLabel = createBtn ? createBtn.innerHTML : '';

    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khởi tạo luồng AI...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(payload, threadId);
    }

    try {
        registerActiveStream(threadId, payload, 'live');
        appendStreamingProgress('bootstrap', 'Đã tạo thread_id, đang yêu cầu backend bắt đầu lập lịch trình…');
        await bootstrapTravelPlanStream(payload, threadId);
    } catch (error) {
        console.error('Create final plan stream error:', error);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = buildSafeFallbackStep4Data(
                payload,
                error.message || 'Không thể hoàn thiện lịch trình AI.'
            );
        }
        displayStep4Result(workflowState.step4Data);
        showErrorModal(error.message || 'Không thể hoàn tất lịch trình lúc này. Vui lòng thử lại.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalLabel;
        }
    }
}

async function resumeTravelPlanStreamFromStorage() {
    const persisted = loadPersistedTravelStream();
    if (!persisted?.threadId || !persisted?.payload) return;

    hydrateWorkflowStateFromPayload(persisted.payload);
    workflowState.step4Data = workflowState.step4Data || { status: 'streaming' };
    goToStep(4);

    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(persisted.payload, persisted.threadId);
    }
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khôi phục luồng AI...';
    }

    registerActiveStream(persisted.threadId, persisted.payload, 'resume');
    appendStreamingProgress('resume', 'Đã tìm thấy thread_id trước đó, đang phát lại tiến độ…');

    try {
        await preflightTravelPlanStream(persisted.threadId);
    } catch (error) {
        cleanupActiveStream({ clearStorage: true, clearData: true });
        showErrorModal(error.message || 'Không thể khôi phục luồng AI.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lịch trình';
        }
        return;
    }

    connectTravelPlanEventSource(persisted.threadId);
}

window.goToStep = goToStep;
window.createFinalPlan = createFinalPlan;
window.closeErrorModal = closeErrorModal;

document.addEventListener('DOMContentLoaded', () => {
    const step4Header = document.querySelector('#step-4 .step-header h2');
    const step4Intro = document.querySelector('#step-4 .step-header p');
    const step4Notice = document.querySelector('#step-4 .tp-soft');
    const modalTitle = document.querySelector('#error-modal-overlay .error-modal-header h3');
    const modalButton = document.querySelector('#error-modal-overlay .error-modal-btn');

    if (step4Header) {
        step4Header.textContent = 'Rà soát blueprint chuyến đi trước khi hoàn tất';
    }
    if (step4Intro) {
        step4Intro.textContent = 'Xem lại tổng chi phí, hoạt động gợi ý và timeline từng ngày. Khi bạn bấm tạo lịch trình, Atlas sẽ phát tiến độ theo thời gian thực và tự khôi phục nếu trang bị tải lại giữa chừng.';
    }
    if (step4Notice) {
        step4Notice.innerHTML = '<strong class="text-slate-900 dark:text-slate-100">Lưu ý chính xác:</strong> Nút <em>Tạo lịch trình</em> sẽ mở luồng AI theo thời gian thực, phát từng ngày khi sẵn sàng và đồng bộ với trạng thái lưu lịch trình ở backend.';
    }
    if (modalTitle) {
        modalTitle.textContent = 'Thông báo';
    }
    if (modalButton) {
        modalButton.textContent = 'Đã hiểu';
    }
});

function renderStreamingSkeletonDays(totalDays) {
    return Array.from({ length: totalDays }, (_, index) => `
        <article id="stream-day-skeleton-${index + 1}" class="timeline-day transition-all duration-300 ease-out opacity-80">
            <div class="timeline-day-header">
                <div>
                    <h4 class="text-base font-bold text-foreground">Ngày ${index + 1}</h4>
                    <div class="timeline-day-meta">
                        <span class="timeline-chip">Đang chờ AI hoàn thiện</span>
                    </div>
                </div>
                <span class="day-toggle-icon theme-text-muted">
                    <i class="fa-solid fa-hourglass-half"></i>
                </span>
            </div>
            <div class="timeline-day-body" style="display:block;">
                <div class="timeline-sections">
                    <div class="loading-line lg"></div>
                    <div class="loading-line md" style="margin-top:0.85rem;"></div>
                </div>
            </div>
        </article>
    `).join('');
}

function renderStep4StreamingShell(payload, threadId) {
    const totalDays = Math.max(1, Number(payload?.days || payload?.duration_days || 1));
    return `
        <div class="step4-shell">
            ${renderStepPanel({
                icon: 'fa-solid fa-tower-broadcast',
                title: 'Atlas đang phát lịch trình theo thời gian thực',
                subtitle: 'Luồng AI sẽ tự khôi phục nếu bạn tải lại trang trong lúc hệ thống còn giữ thread.',
                content: `
                    <div class="plan-overview-grid transition-all duration-300 ease-out">
                        <article class="plan-overview-card">
                            <span class="summary-label">Thread</span>
                            <span class="summary-value">${escapeHtml(threadId)}</span>
                        </article>
                        <article class="plan-overview-card">
                            <span class="summary-label">Tuyến hành trình</span>
                            <span class="summary-value">${escapeHtml(`${payload.origin || 'Điểm đi'} → ${payload.destination || 'Điểm đến'}`)}</span>
                        </article>
                        <article class="plan-overview-card">
                            <span class="summary-label">Trạng thái</span>
                            <span id="step4-stream-status" class="summary-value">Đang khởi tạo luồng AI…</span>
                        </article>
                    </div>
                    <div id="step4-stream-progress" class="timeline-list mt-5 transition-all duration-300 ease-out">
                        <div class="itinerary-activity">Đang chuẩn bị kết nối tới máy chủ phát trực tuyến…</div>
                    </div>
                `
            })}
            ${renderStepPanel({
                icon: 'fa-solid fa-calendar-days',
                title: 'Ngày đã hoàn thiện',
                subtitle: 'Mỗi thẻ sẽ thay thế skeleton ngay khi backend phát sự kiện day_ready.',
                content: `<div id="step4-stream-days" class="timeline-shell transition-all duration-300 ease-out">${renderStreamingSkeletonDays(totalDays)}</div>`
            })}
        </div>
    `;
}

function renderStreamingTimelineItem(item) {
    if (!item || typeof item !== 'object') {
        return '';
    }

    const time = escapeHtml(item.time || item.time_slot || '');
    const activityName = escapeHtml(item.activity_name || item.activity || 'Hoạt động');
    const note = escapeHtml(item.note || item.description || '');
    const placeName = escapeHtml(item.place_name || '');

    return `
        <article class="itinerary-activity transition-all duration-300 ease-out">
            ${time ? `<div class="timeline-chip">${time}</div>` : ''}
            <div class="mt-2 text-sm font-semibold text-foreground">${activityName}</div>
            ${placeName ? `<div class="budget-inline-meta">Địa điểm: ${placeName}</div>` : ''}
            ${note ? `<div class="budget-inline-meta">${note}</div>` : ''}
        </article>
    `;
}

function upsertStreamingDayCard(dayPayload) {
    const container = document.getElementById('step4-stream-days');
    if (!container || !dayPayload) return;

    const dayNumber = Number(dayPayload.day || 0) || 1;
    const cardId = `stream-day-card-${dayNumber}`;
    const skeleton = document.getElementById(`stream-day-skeleton-${dayNumber}`);
    const existing = document.getElementById(cardId);
    const timeline = Array.isArray(dayPayload.timeline) ? dayPayload.timeline : [];

    const markup = `
        <article id="${cardId}" class="timeline-day transition-all duration-300 ease-out">
            <div class="timeline-day-header">
                <div>
                    <h4 class="text-base font-bold text-foreground">📅 Ngày ${dayNumber}${dayPayload.date ? ` (${escapeHtml(dayPayload.date)})` : ''}${dayPayload.theme ? `: ${escapeHtml(dayPayload.theme)}` : ''}</h4>
                    <div class="timeline-day-meta">
                        <span class="timeline-chip"><i class="fa-regular fa-clock"></i> ${timeline.length} mốc hoạt động</span>
                        <span class="timeline-chip"><i class="fa-solid fa-check"></i> Đã sẵn sàng</span>
                    </div>
                </div>
            </div>
            <div class="timeline-day-body" style="display:block;">
                <div class="timeline-sections">
                    <section class="timeline-section">
                        <div class="timeline-section-title">
                            <i class="fa-solid fa-map-location-dot"></i>
                            <span>Lộ trình trong ngày</span>
                        </div>
                        <div class="timeline-list">
                            ${timeline.length ? timeline.map(renderStreamingTimelineItem).join('') : renderEmptyState('AI chưa gửi chi tiết timeline cho ngày này.')}
                        </div>
                    </section>
                </div>
            </div>
        </article>
    `;

    if (existing) {
        existing.outerHTML = markup;
    } else if (skeleton) {
        skeleton.outerHTML = markup;
    } else {
        container.insertAdjacentHTML('beforeend', markup);
    }
}

function appendStreamingProgress(step, message) {
    const progressContainer = document.getElementById('step4-stream-progress');
    const statusNode = document.getElementById('step4-stream-status');
    if (statusNode && message) {
        statusNode.textContent = message;
    }
    if (!progressContainer || !message) return;

    const progressKey = `${step || 'general'}:${message}`;
    if (workflowState.streamedProgressKeys.has(progressKey)) {
        return;
    }
    workflowState.streamedProgressKeys.add(progressKey);

    progressContainer.insertAdjacentHTML('beforeend', `
        <div class="itinerary-activity transition-all duration-300 ease-out">
            <strong class="block text-sm text-foreground">${escapeHtml(step || 'planning')}</strong>
            <span class="budget-inline-meta">${escapeHtml(message)}</span>
        </div>
    `);
}

function cleanupActiveStream({ clearStorage = true, clearData = false } = {}) {
    if (workflowState.activeStream?.eventSource) {
        workflowState.activeStream.eventSource.close();
    }

    if (workflowState.postStreamReconnectTimer) {
        window.clearTimeout(workflowState.postStreamReconnectTimer);
        workflowState.postStreamReconnectTimer = null;
    }

    workflowState.activeStream = null;
    resetStreamTrackingState();

    if (clearStorage) {
        clearPersistedTravelStream();
    }

    if (clearData) {
        workflowState.step4Data = null;
    }
}

function handleStreamEvent(eventType, payload) {
    if (!payload || typeof payload !== 'object') return;

    if (eventType === 'connected') {
        appendStreamingProgress('connected', payload.message || 'Đã kết nối tới luồng SSE.');
        return;
    }

    if (eventType === 'progress') {
        appendStreamingProgress(payload.step, payload.message || 'Đang xử lý lịch trình.');
        return;
    }

    if (eventType === 'day_ready') {
        upsertStreamingDayCard(payload);
        appendStreamingProgress('day_ready', `Đã hoàn thiện ngày ${payload.day}.`);
        return;
    }

    if (eventType === 'completed') {
        if (workflowState.activeStream) {
            workflowState.activeStream.status = 'completed';
        }
        workflowState.step4Data = payload.response || payload;
        displayStep4Result(workflowState.step4Data);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        showErrorModal('Lịch trình đã được tạo thành công.', 'success');
        const createBtn = document.getElementById('step4-create');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i>Tạo lại lịch trình';
        }
        return;
    }

    if (eventType === 'error') {
        appendStreamingProgress('error', payload.message || STREAM_FAILURE_MESSAGE);
        cleanupActiveStream({ clearStorage: false, clearData: false });
        showErrorModal(payload.message || STREAM_FAILURE_MESSAGE);
        const createBtn = document.getElementById('step4-create');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lịch trình';
        }
    }
}

function registerActiveStream(threadId, payload, mode = 'live') {
    workflowState.activeStream = {
        threadId,
        payload,
        mode,
        eventSource: null,
        status: 'running'
    };
    resetStreamTrackingState();
    persistActiveTravelStream({
        threadId,
        payload,
        mode,
        savedAt: new Date().toISOString()
    });
}

function connectTravelPlanEventSource(threadId) {
    const streamUrl = `/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`;
    const eventSource = new EventSource(streamUrl);

    if (!workflowState.activeStream) {
        workflowState.activeStream = { threadId, eventSource, status: 'running' };
    } else {
        workflowState.activeStream.eventSource = eventSource;
        workflowState.activeStream.status = 'running';
    }

    ['connected', 'progress', 'day_ready', 'completed', 'error'].forEach((eventName) => {
        eventSource.addEventListener(eventName, (event) => {
            let payload = {};
            try {
                payload = event.data ? JSON.parse(event.data) : {};
            } catch (error) {
                console.error('Không thể parse SSE payload:', error, event.data);
            }
            handleStreamEvent(eventName, payload);
        });
    });

    eventSource.onerror = () => {
        if (!workflowState.activeStream || workflowState.activeStream.threadId !== threadId) {
            eventSource.close();
            return;
        }

        eventSource.close();
        workflowState.activeStream.eventSource = null;

        if (workflowState.activeStream.status === 'completed') {
            return;
        }

        appendStreamingProgress('reconnect', 'Luồng SSE bị gián đoạn, đang thử kết nối lại…');
        workflowState.postStreamReconnectTimer = window.setTimeout(() => {
            connectTravelPlanEventSource(threadId);
        }, 1200);
    };
}

async function bootstrapTravelPlanStream(payload, threadId) {
    const response = await fetch('/api/v1/travel-plans/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            ...payload,
            thread_id: threadId
        })
    });

    if (!response.ok) {
        let errorPayload = {};
        try {
            errorPayload = await parseJsonResponse(response, 'Không thể khởi tạo luồng AI.');
        } catch (error) {
            throw new Error(error.message || 'Không thể khởi tạo luồng AI.');
        }
        throw new Error(errorPayload.error || 'Không thể khởi tạo luồng AI.');
    }

    if (response.body?.cancel) {
        try {
            await response.body.cancel();
        } catch (error) {
            console.warn('Không thể đóng bootstrap stream phụ.', error);
        }
    }

    connectTravelPlanEventSource(threadId);
}

function goToStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');

        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });

    workflowState.currentStep = step;

    if (step === 3 && !workflowState.step3Data) {
        loadStep3();
    } else if (step === 4 && !workflowState.step4Data && !workflowState.activeStream) {
        loadStep4();
    }
}

async function createFinalPlan() {
    const createBtn = document.getElementById('step4-create');
    const resultDiv = document.getElementById('step4-result');
    const payload = buildStep4GenerationPayload();

    if (!payload.origin || !payload.destination || !payload.start_date) {
        showErrorModal('Thiếu dữ liệu hành trình. Vui lòng kiểm tra lại 4 bước trước khi tạo lịch trình.');
        return;
    }

    if (workflowState.activeStream?.threadId) {
        showErrorModal('Luồng AI hiện tại vẫn đang chạy. Vui lòng chờ hoàn tất hoặc tải lại trang để khôi phục.');
        return;
    }

    const threadId = generateTravelPlanThreadId();
    const originalLabel = createBtn ? createBtn.innerHTML : '';

    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khởi tạo luồng AI...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(payload, threadId);
    }

    try {
        registerActiveStream(threadId, payload, 'live');
        appendStreamingProgress('bootstrap', 'Đã tạo thread_id, đang yêu cầu backend bắt đầu lập lịch trình…');
        await bootstrapTravelPlanStream(payload, threadId);
    } catch (error) {
        console.error('Create final plan stream error:', error);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = buildSafeFallbackStep4Data(
                payload,
                error.message || 'Không thể hoàn thiện lịch trình AI.'
            );
        }
        displayStep4Result(workflowState.step4Data);
        showErrorModal(error.message || 'Không thể hoàn tất lịch trình lúc này. Vui lòng thử lại.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalLabel;
        }
    }
}

function resumeTravelPlanStreamFromStorage() {
    const persisted = loadPersistedTravelStream();
    if (!persisted?.threadId || !persisted?.payload) return;

    hydrateWorkflowStateFromPayload(persisted.payload);
    workflowState.step4Data = workflowState.step4Data || { status: 'streaming' };
    goToStep(4);

    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(persisted.payload, persisted.threadId);
    }
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khôi phục luồng AI...';
    }

    registerActiveStream(persisted.threadId, persisted.payload, 'resume');
    appendStreamingProgress('resume', 'Đã tìm thấy thread_id trước đó, đang phát lại tiến độ…');
    connectTravelPlanEventSource(persisted.threadId);
}

window.goToStep = goToStep;
window.createFinalPlan = createFinalPlan;

function buildLoginUrl() {
    const nextUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    return `${LOGIN_PATH}?next=${encodeURIComponent(nextUrl)}`;
}

function redirectToLogin() {
    window.location.assign(buildLoginUrl());
}

function handleProtectedRouteFailure() {
    if (workflowState.authRedirectPending) return;
    workflowState.authRedirectPending = true;

    showErrorModal(AUTH_REQUIRED_MESSAGE, 'error', {
        onClose: redirectToLogin
    });

    window.setTimeout(() => {
        if (workflowState.authRedirectPending) {
            redirectToLogin();
        }
    }, 1400);
}

function persistActiveTravelStream(payload) {
    try {
        window.sessionStorage.setItem(ACTIVE_TRAVEL_STREAM_STORAGE_KEY, JSON.stringify(payload));
    } catch (error) {
        console.warn('Không thể lưu thread_id của luồng hiện tại.', error);
    }
}

function loadPersistedTravelStream() {
    try {
        const raw = window.sessionStorage.getItem(ACTIVE_TRAVEL_STREAM_STORAGE_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (error) {
        console.warn('Không thể đọc thread_id đã lưu.', error);
        return null;
    }
}

function clearPersistedTravelStream() {
    try {
        window.sessionStorage.removeItem(ACTIVE_TRAVEL_STREAM_STORAGE_KEY);
    } catch (error) {
        console.warn('Không thể xoá thread_id đã lưu.', error);
    }
}

function displayStep1Result(data) {
    const resultDiv = document.getElementById('step1-result');
    if (!resultDiv) return;
    
    resultDiv.innerHTML = `
        <div class="info-card">
            <h4>✅ Thông tin địa điểm</h4>
            <p><strong>Điểm đi:</strong> ${data.origin.name}</p>
            <p><strong>Điểm đến:</strong> ${data.destination.name}</p>
            <p><strong>Khoảng cách:</strong> ${data.distance_km} km</p>
            <p><strong>Thời gian di chuyển:</strong> ${data.estimated_duration}</p>
            <p><strong>Phương tiện đề xuất:</strong> ${data.transport_icon} ${data.recommended_transport}</p>
        </div>
    `;
    resultDiv.style.display = 'block';
}

// Step 2: Travel Info
async function handleStep2Submit(e) {
    // Prevent default form submission
    e.preventDefault();
    e.stopPropagation();
    
    const startDateInput = document.getElementById('start-date');
    const startDateValue = startDateInput ? startDateInput.value : '';
    
    // Convert date from d/m/Y to YYYY-MM-DD for API
    let startDate = '';
    if (startDateValue) {
        const dateParts = startDateValue.split('/');
        if (dateParts.length === 3) {
            // Format: d/m/Y -> YYYY-MM-DD
            const day = dateParts[0].padStart(2, '0');
            const month = dateParts[1].padStart(2, '0');
            const year = dateParts[2];
            startDate = `${year}-${month}-${day}`;
        } else {
            // Try to parse as-is if already in correct format
            startDate = startDateValue;
        }
    }
    
    const days = parseInt(document.getElementById('days').value);
    const travelers = parseInt(document.getElementById('travelers').value);
    const travelStyle = document.getElementById('travel-style').value;
    
    // Prevent default submission first
    e.preventDefault();
    e.stopPropagation();
    
    // Validate required fields
    if (!startDate || !days || !travelers || !travelStyle) {
        showErrorModal('Vui lòng điền đầy đủ thông tin');
        return false;
    }
    
    // Validate days (1-14)
    if (days < 1) {
        showErrorModal('Số ngày phải lớn hơn 0');
        // Keep current step, don't proceed
        return false;
    }
    
    if (days > 14) {
        showErrorModal('Số ngày không được vượt quá 14 ngày');
        // Keep current step, don't proceed
        return false;
    }
    
    // Validate travelers (1-20)
    if (travelers < 1) {
        showErrorModal('Số người phải lớn hơn 0');
        // Keep current step, don't proceed
        return false;
    }
    
    if (travelers > 20) {
        showErrorModal('Số người không được vượt quá 20 người (tương ứng với 1 gia đình)');
        // Keep current step, don't proceed
        return false;
    }
    
    // Only proceed with submission if validation passes
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Đang tải...';
    
    try {
        const response = await fetch('/api/v1/travel-plans/step2/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                origin: workflowState.step1Data.origin.name,
                destination: workflowState.step1Data.destination.name,
                start_date: startDate,
                days: days,
                travelers: travelers
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            workflowState.step2Data = {
                ...data,
                start_date: startDate,
                days: days,
                travelers: travelers,
                travel_style: travelStyle
            };
            displayStep2Result(data);
            setTimeout(() => {
                goToStep(3);
                loadStep3();
            }, 1000);
        } else {
            // Backend validation error or other error
            showErrorModal('Lỗi: ' + (data.error || 'Không thể xử lý yêu cầu'));
            // Keep current step, don't proceed - stay on Step 2
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            return false;
        }
    } catch (error) {
        console.error('Step 2 error:', error);
        showErrorModal('Lỗi kết nối. Vui lòng thử lại.');
        // Keep current step, don't proceed - stay on Step 2
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
        return false;
    }
}

function displayStep2Result(data) {
    const resultDiv = document.getElementById('step2-result');
    if (!resultDiv) return;
    
    const transport = data.transport || {};
    const options = transport.options || [];
    
    let optionsHTML = '';
    if (options.length > 0) {
        optionsHTML = '<div class="transport-options">';
        options.forEach(opt => {
            optionsHTML += `
                <div class="transport-option">
                    <div class="transport-option-icon">${opt.icon}</div>
                    <div><strong>${opt.name}</strong></div>
                    <div style="font-size: 0.9rem; color: var(--color-gray-600);">
                        ${opt.estimated_time} - ${formatCurrency(opt.estimated_cost_vnd)} VNĐ
                    </div>
                </div>
            `;
        });
        optionsHTML += '</div>';
    }
    
    resultDiv.innerHTML = `
        <div class="info-card">
            <h4>✈️ Thông tin vận chuyển</h4>
            <p><strong>Khoảng cách:</strong> ${transport.distance_km || 0} km</p>
            <p><strong>Thời gian:</strong> ${(transport.duration_minutes / 60).toFixed(1)}h</p>
            <p><strong>Phương tiện đề xuất:</strong> ${data.recommended_transport}</p>
            ${optionsHTML}
        </div>
        <div class="info-card">
            <h4>📅 Thời gian</h4>
            <p><strong>Số ngày đề xuất:</strong> ${data.recommended_days || workflowState.step2Data.days} ngày</p>
        </div>
    `;
    resultDiv.style.display = 'block';
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderEmptyState(message) {
    return `<div class="empty-state-card">${escapeHtml(message)}</div>`;
}

function renderStepPanel({ icon, title, subtitle, content }) {
    return `
        <section class="step-panel">
            <div class="step-panel-header">
                <span class="step-panel-icon"><i class="${icon}"></i></span>
                <div>
                    <h3 class="step-panel-title">${escapeHtml(title)}</h3>
                    <p class="step-panel-subtitle">${escapeHtml(subtitle)}</p>
                </div>
            </div>
            ${content}
        </section>
    `;
}

// Step 3: Budget & Hotels
async function loadStep3() {
    const resultDiv = document.getElementById('step3-result');
    const continueBtn = document.getElementById('step3-continue');
    
    if (!resultDiv) return;
    
    resultDiv.innerHTML = `
        <div class="step3-shell">
            <div class="step3-grid">
                ${renderStepPanel({
                    icon: 'fa-solid fa-wallet',
                    title: 'Bức tranh ngân sách',
                    subtitle: 'Atlas đang phân tích các nhóm chi phí cốt lõi cho chuyến đi của bạn.',
                    content: '<div class="loading-line lg"></div><div class="loading-line md" style="margin-top:0.85rem;"></div><div class="loading-line sm" style="margin-top:0.85rem;"></div>'
                })}
                ${renderStepPanel({
                    icon: 'fa-solid fa-hotel',
                    title: 'Khách sạn được tuyển chọn',
                    subtitle: 'Danh sách lưu trú đang được xếp theo mức phù hợp với lịch trình và phong cách.',
                    content: '<div class="loading-line lg"></div><div class="loading-line md" style="margin-top:0.85rem;"></div><div class="loading-line sm" style="margin-top:0.85rem;"></div>'
                })}
            </div>
        </div>
    `;
    
    try {
        const response = await fetch('/api/v1/travel-plans/step3/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                origin: workflowState.step1Data.origin.name,
                destination: workflowState.step1Data.destination.name,
                start_date: workflowState.step2Data.start_date,
                days: workflowState.step2Data.days,
                travelers: workflowState.step2Data.travelers,
                travel_style: workflowState.step2Data.travel_style,
                rooms: 1
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            workflowState.step3Data = data;
            displayStep3Result(data);
            if (continueBtn) continueBtn.disabled = false;
        } else {
            resultDiv.innerHTML = renderEmptyState(`Không thể tải dữ liệu bước 3: ${data.error || 'Vui lòng thử lại.'}`);
        }
    } catch (error) {
        console.error('Step 3 error:', error);
        resultDiv.innerHTML = renderEmptyState('Lỗi kết nối khi tải ngân sách và khách sạn. Vui lòng thử lại.');
    }
}

function displayStep3Result(data) {
    const resultDiv = document.getElementById('step3-result');
    if (!resultDiv) return;
    
    const budget = data.budget || {};
    const breakdown = budget.breakdown || {};
    const hotels = data.hotels || [];
    
    let budgetHTML = renderEmptyState('Chưa có dữ liệu ngân sách chi tiết cho hành trình này.');
    if (budget.total_vnd) {
        budgetHTML = `
            <div class="budget-grid">
                <article class="budget-stat-card">
                    <span class="budget-stat-label">Di chuyển</span>
                    <span class="budget-stat-value">${formatCurrency(breakdown.transport || 0)} VNĐ</span>
                </article>
                <article class="budget-stat-card">
                    <span class="budget-stat-label">Lưu trú</span>
                    <span class="budget-stat-value">${formatCurrency(breakdown.accommodation || 0)} VNĐ</span>
                </article>
                <article class="budget-stat-card">
                    <span class="budget-stat-label">Ăn uống</span>
                    <span class="budget-stat-value">${formatCurrency(breakdown.dining || 0)} VNĐ</span>
                </article>
                <article class="budget-stat-card">
                    <span class="budget-stat-label">Hoạt động</span>
                    <span class="budget-stat-value">${formatCurrency(breakdown.activities || 0)} VNĐ</span>
                </article>
                <article class="budget-stat-card">
                    <span class="budget-stat-label">Bình quân / người</span>
                    <span class="budget-stat-value">${formatCurrency(budget.per_person || 0)} VNĐ</span>
                </article>
                <article class="budget-stat-card is-highlight">
                    <span class="budget-stat-label">Tổng ngân sách</span>
                    <span class="budget-stat-value">${formatCurrency(budget.total_vnd)} VNĐ</span>
                    <span class="budget-inline-meta">Khoảng ${formatCurrency(budget.per_day || 0)} VNĐ / ngày cho toàn bộ lịch trình.</span>
                </article>
            </div>
        `;
    }
    
    let hotelsHTML = renderEmptyState('Chưa có khách sạn phù hợp được trả về ở bước này.');
    if (hotels.length > 0) {
        hotelsHTML = `
            <div class="hotels-grid">
                ${hotels.map((hotel, index) => {
                    let imageUrl = '';
                    if (hotel.images && hotel.images.length > 0) imageUrl = hotel.images[0];
                    else if (hotel.image_url) imageUrl = hotel.image_url;
                    else if (hotel.thumbnail) imageUrl = hotel.thumbnail;

                    return `
                        <article class="hotel-card" onclick="selectHotel(${index})" data-hotel-index="${index}">
                            <div class="hotel-card-shell">
                                ${imageUrl ? `
                                    <div class="hotel-media">
                                        <img src="${imageUrl}" alt="${escapeHtml(hotel.name || 'Khách sạn')}" onerror="this.closest('.hotel-media').style.display='none'">
                                    </div>
                                ` : ''}
                                <div>
                                    <div class="hotel-header">
                                        <div>
                                            <div class="hotel-name">${escapeHtml(hotel.name || 'Chưa có tên khách sạn')}</div>
                                            ${hotel.stars ? `<div class="budget-inline-meta">${'⭐'.repeat(hotel.stars)} ${hotel.rating || ''}/5 ${hotel.reviews ? `(${hotel.reviews} đánh giá)` : ''}</div>` : ''}
                                        </div>
                                        ${hotel.price_per_night ? `<div class="hotel-price">${formatCurrency(hotel.price_per_night)} VNĐ/đêm</div>` : ''}
                                    </div>
                                    <div class="hotel-meta-list">
                                        ${hotel.hotel_class ? `<span>${escapeHtml(hotel.hotel_class)} sao</span>` : ''}
                                        ${hotel.address ? `<span>📍 ${escapeHtml(hotel.address)}</span>` : ''}
                                        ${hotel.phone ? `<span>📞 ${escapeHtml(hotel.phone)}</span>` : ''}
                                        ${hotel.email ? `<span>✉️ ${escapeHtml(hotel.email)}</span>` : ''}
                                        ${hotel.source ? `<span>Nguồn: ${escapeHtml(hotel.source)}</span>` : ''}
                                        ${hotel.website ? `<span><a href="${hotel.website}" target="_blank" onclick="event.stopPropagation();">🌐 Xem website</a></span>` : ''}
                                    </div>
                                    ${hotel.description ? `<p class="budget-inline-meta">${escapeHtml(hotel.description.substring(0, 180))}${hotel.description.length > 180 ? '...' : ''}</p>` : ''}
                                    ${hotel.amenities && hotel.amenities.length > 0 ? `
                                        <div class="hotel-amenities">
                                            ${hotel.amenities.slice(0, 5).map((amenity) => `<span class="hotel-amenity">${escapeHtml(amenity)}</span>`).join('')}
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        </article>
                    `;
                }).join('')}
            </div>
        `;
    }
    
    resultDiv.innerHTML = `
        <div class="step3-shell">
            <div class="step3-grid">
                ${renderStepPanel({
                    icon: 'fa-solid fa-wallet',
                    title: 'Bức tranh ngân sách',
                    subtitle: 'Chi phí được chia theo từng nhóm chính để bạn cân đối nhanh trước khi chốt kế hoạch.',
                    content: budgetHTML
                })}
                ${renderStepPanel({
                    icon: 'fa-solid fa-hotel',
                    title: 'Khách sạn được tuyển chọn',
                    subtitle: 'Chọn một nơi lưu trú nếu bạn muốn Atlas ưu tiên gắn vào blueprint cuối cùng.',
                    content: hotelsHTML
                })}
            </div>
        </div>
    `;
}

function selectHotel(index) {
    // Remove previous selection
    document.querySelectorAll('.hotel-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Mark as selected
    const card = document.querySelector(`[data-hotel-index="${index}"]`);
    if (card) {
        card.classList.add('selected');
        workflowState.step3Data.selected_hotel = workflowState.step3Data.hotels[index];
    }
}

// Step 4: Confirm & Create Plan
async function loadStep4() {
    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    
    if (!resultDiv) return;
    
    resultDiv.innerHTML = renderStep4LoadingState();
    
    try {
        const payload = buildStep4GenerationPayload();
        const data = await requestStep4Plan(payload);

        workflowState.step4Data = data;
        displayStep4Result(data);
        if (createBtn) createBtn.disabled = false;
    } catch (error) {
        console.error('Step 4 error:', error);
        const fallbackData = buildSafeFallbackStep4Data(
            buildStep4GenerationPayload(),
            'Không thể kết nối tới bộ tạo lịch trình. Hệ thống đã dựng bản xem trước an toàn để bạn tiếp tục.'
        );
        workflowState.step4Data = fallbackData;
        displayStep4Result(fallbackData);
        if (createBtn) createBtn.disabled = false;
    }
}

function displayStep4Result(data) {
    const resultDiv = document.getElementById('step4-result');
    if (!resultDiv) return;
    
    const plan = data.plan || {};
    const costs = data.costs || {};
    const activities = plan.activities || [];
    const itinerary = plan.itinerary || {};
    // Support both daily_plans and itinerary array format
    const dailyPlans = itinerary.daily_plans || itinerary.itinerary || [];
    
    // Get destination from workflow state
    const destination = workflowState.step1Data?.destination?.name || plan.destination || itinerary.destination || 'Điểm đến';
    
    // Get total days - prioritize from itinerary, then dailyPlans length, then workflow state
    const totalDays = itinerary.total_days || dailyPlans.length || workflowState.step1Data?.days || 0;
    
    const startDateText = document.getElementById('start-date')?.value || 'Chưa chọn ngày đi';
    const travelers = workflowState.step2Data?.travelers || 0;
    const styleLabel = document.getElementById('travel-style-display')?.value || 'Tiêu chuẩn';
    const selectedHotel = workflowState.step3Data?.selected_hotel?.name || 'Bạn có thể tiếp tục mà không chọn khách sạn';
    const routeLabel = `${workflowState.step1Data?.origin?.name || 'Điểm đi'} → ${destination}`;
    
    let activitiesHTML = '';
    if (activities.length > 0) {
        activitiesHTML = `
            <div class="timeline-list">
                ${activities.slice(0, 6).map(activity => `
                    <article class="itinerary-activity">
                        <strong class="block text-sm text-foreground">${escapeHtml(activity.name || 'Hoạt động')}</strong>
                        ${activity.description ? `<p class="budget-inline-meta">${escapeHtml(activity.description)}</p>` : ''}
                        ${activity.cost_vnd ? `<p class="budget-inline-meta">Chi phí ước tính: ${formatCurrency(activity.cost_vnd)} VNĐ</p>` : ''}
                    </article>
                `).join('')}
            </div>
        `;
    }
    
    let itineraryHTML = '';
    if (dailyPlans.length > 0) {
        itineraryHTML = `
            <div class="timeline-shell">
                    ${dailyPlans.map((dayPlan, index) => {
                        const day = dayPlan.day || (index + 1);
                        const date = dayPlan.date || '';
                        const theme = dayPlan.theme || '';
                        const meals = dayPlan.meals || {};
                        const activities_list = dayPlan.activities || [];
                        const tips = dayPlan.tips || [];
                        const dayId = `day-${index}`;
                        
                        // Count activities
                        const activityCount = activities_list.length;
                        const totalHours = Math.ceil(activityCount * 1.5); // Estimate
                        
                        let mealsHTML = '';
                        if (meals && Object.keys(meals).length > 0) {
                            const mealLabels = {
                                breakfast: 'Sáng',
                                lunch: 'Trưa',
                                dinner: 'Tối',
                                snacks: 'Ăn vặt',
                                drinks: 'Giải khát',
                                afternoon_tea: 'Trà chiều'
                            };
                            mealsHTML = '<section class="timeline-section"><div class="timeline-section-title"><i class="fa-solid fa-utensils"></i><span>Bữa ăn & điểm nghỉ</span></div><div class="timeline-list">';
                            Object.keys(mealLabels).forEach(mealType => {
                                if (meals[mealType]) {
                                    const meal = meals[mealType];
                                    const mealName = typeof meal === 'string' ? meal : (meal.name || 'N/A');
                                    mealsHTML += `<div class="budget-inline-meta"><strong>${mealLabels[mealType]}:</strong> ${escapeHtml(mealName)}</div>`;
                                }
                            });
                            mealsHTML += '</div></section>';
                        }
                        
                        let activitiesHTML_day = '';
                        if (activities_list.length > 0) {
                            activitiesHTML_day = '<section class="timeline-section"><div class="timeline-section-title"><i class="fa-solid fa-map-marker-alt"></i><span>Hoạt động theo khung giờ</span></div><div class="timeline-list">';
                            activities_list.forEach(actItem => {
                                if (typeof actItem === 'string') {
                                    activitiesHTML_day += `<div class="itinerary-activity"><div class="text-sm font-semibold text-foreground">${escapeHtml(actItem)}</div></div>`;
                                } else if (typeof actItem === 'object') {
                                    const time = actItem.time || actItem.time_slot || '';
                                    const actDesc = actItem.description || '';
                                    const activity = actItem.activity || {};
                                    const actName = typeof activity === 'string' ? activity : (activity.name || 'Hoạt động');
                                    
                                    activitiesHTML_day += `<div class="itinerary-activity">`;
                                    if (time) {
                                        activitiesHTML_day += `<div class="timeline-chip">${escapeHtml(time)}</div>`;
                                    }
                                    activitiesHTML_day += `<div class="mt-2 text-sm font-semibold text-foreground">${escapeHtml(actName)}</div>`;
                                    if (actDesc) {
                                        activitiesHTML_day += `<div class="budget-inline-meta">${escapeHtml(actDesc)}</div>`;
                                    }
                                    activitiesHTML_day += `</div>`;
                                }
                            });
                            activitiesHTML_day += '</div></section>';
                        }
                        
                        let tipsHTML = '';
                        if (tips.length > 0) {
                            tipsHTML = '<section class="timeline-section"><div class="timeline-section-title"><i class="fa-solid fa-lightbulb"></i><span>Mẹo địa phương</span></div><ul class="timeline-note-list">';
                            tips.slice(0, 3).forEach(tip => {
                                tipsHTML += `<li>${escapeHtml(tip)}</li>`;
                            });
                            tipsHTML += '</ul></section>';
                        }
                        
                        return `
                            <article class="timeline-day">
                                <div class="timeline-day-header" onclick="toggleDay('${dayId}')">
                                    <div>
                                        <h4 class="text-base font-bold text-foreground">
                                            📆 Ngày ${day}${date ? ` (${date})` : ''}${theme ? `: ${theme}` : ''}
                                        </h4>
                                        <div class="timeline-day-meta">
                                            <span class="timeline-chip"><i class="fa-regular fa-clock"></i> ${activityCount} hoạt động</span>
                                            <span class="timeline-chip"><i class="fa-solid fa-hourglass-half"></i> ${totalHours} tiếng</span>
                                            ${theme ? `<span class="timeline-chip"><i class="fa-solid fa-star"></i> ${escapeHtml(theme)}</span>` : ''}
                                        </div>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <span class="day-toggle-icon theme-text-muted" id="icon-${dayId}" style="font-size: 1.2rem; transition: transform 0.3s; cursor: pointer;">
                                            <i class="fa-solid fa-chevron-down"></i>
                                        </span>
                                    </div>
                                </div>
                                <div class="timeline-day-body" id="${dayId}" style="display: none;">
                                    <div class="timeline-sections">
                                        ${activitiesHTML_day}
                                        ${mealsHTML}
                                        ${tipsHTML}
                                    </div>
                                </div>
                            </article>
                        `;
                    }).join('')}
            </div>
        `;
    } else {
        itineraryHTML = renderEmptyState('Chưa có timeline chi tiết theo ngày được tạo ra ở bước này.');
    }
    
    resultDiv.innerHTML = `
        <div class="step4-shell">
            ${renderStepPanel({
                icon: 'fa-solid fa-map-location-dot',
                title: 'Tổng quan hành trình',
                subtitle: 'Rà soát nhanh lộ trình, thời gian khởi hành, phong cách và khách sạn đã chọn trước khi hoàn tất.',
                content: `
                    <div class="plan-overview-grid">
                        <article class="plan-overview-card"><span class="summary-label">Tuyến hành trình</span><span class="summary-value">${escapeHtml(routeLabel)}</span></article>
                        <article class="plan-overview-card"><span class="summary-label">Thời gian</span><span class="summary-value">${escapeHtml(startDateText)} • ${escapeHtml(String(totalDays))} ngày</span></article>
                        <article class="plan-overview-card"><span class="summary-label">Quy mô nhóm</span><span class="summary-value">${escapeHtml(String(travelers))} người</span></article>
                        <article class="plan-overview-card"><span class="summary-label">Phong cách</span><span class="summary-value">${escapeHtml(styleLabel)}</span></article>
                        <article class="plan-overview-card"><span class="summary-label">Khách sạn</span><span class="summary-value">${escapeHtml(selectedHotel)}</span></article>
                        <article class="plan-overview-card"><span class="summary-label">Tổng chi phí</span><span class="summary-value">${formatCurrency(costs.total || 0)} VNĐ</span></article>
                    </div>
                `
            })}
            <div class="step4-grid">
                ${renderStepPanel({
                    icon: 'fa-solid fa-wallet',
                    title: 'Tổng kết chi phí',
                    subtitle: 'Các con số cốt lõi để bạn cân nhanh ngân sách trước khi tạo lịch trình.',
                    content: `
                        <div class="budget-grid">
                            <article class="budget-stat-card"><span class="budget-stat-label">Di chuyển</span><span class="budget-stat-value">${formatCurrency(costs.transport || 0)} VNĐ</span></article>
                            <article class="budget-stat-card"><span class="budget-stat-label">Lưu trú</span><span class="budget-stat-value">${formatCurrency(costs.accommodation || 0)} VNĐ</span></article>
                            <article class="budget-stat-card"><span class="budget-stat-label">Hoạt động</span><span class="budget-stat-value">${formatCurrency(costs.activities || 0)} VNĐ</span></article>
                            <article class="budget-stat-card"><span class="budget-stat-label">Ăn uống</span><span class="budget-stat-value">${formatCurrency(costs.dining || 0)} VNĐ</span></article>
                            <article class="budget-stat-card is-highlight"><span class="budget-stat-label">Tổng cộng</span><span class="budget-stat-value">${formatCurrency(costs.total || 0)} VNĐ</span></article>
                        </div>
                    `
                })}
                ${renderStepPanel({
                    icon: 'fa-solid fa-compass',
                    title: 'Hoạt động nổi bật',
                    subtitle: 'Những điểm nhấn Atlas ưu tiên đẩy lên đầu để chuyến đi cân bằng trải nghiệm và chi phí.',
                    content: activitiesHTML || renderEmptyState('Chưa có hoạt động nổi bật được đề xuất.')
                })}
            </div>
            ${renderStepPanel({
                icon: 'fa-solid fa-calendar-days',
                title: 'Timeline theo ngày',
                subtitle: 'Mở từng ngày để xem hoạt động, bữa ăn và các mẹo bản địa đi kèm.',
                content: itineraryHTML
            })}
        </div>
    `;
}

// Toggle day card
function toggleDay(dayId) {
    const content = document.getElementById(dayId);
    const icon = document.getElementById(`icon-${dayId}`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.innerHTML = '<i class="fa-solid fa-chevron-up"></i>';
        icon.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        icon.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
        icon.style.transform = 'rotate(0deg)';
    }
}

async function createFinalPlan() {
    const createBtn = document.getElementById('step4-create');
    const resultDiv = document.getElementById('step4-result');
    const payload = buildStep4GenerationPayload();

    if (!payload.origin || !payload.destination || !payload.start_date) {
        showErrorModal('Thiếu dữ liệu hành trình. Vui lòng kiểm tra lại 4 bước trước khi lưu lịch trình.');
        return;
    }

    const originalLabel = createBtn ? createBtn.innerHTML : '';
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> AI đang hoàn thiện lịch trình...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = renderStep4LoadingState(
            'Atlas đang khóa blueprint cuối',
            'Dữ liệu từ biểu mẫu đang được chuyển đến AI planner và lưu vào hồ sơ hành trình của bạn.'
        );
    }

    try {
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = await requestStep4Plan(payload);
        }

        const canonicalPlan = workflowState.step4Data.plan?.itinerary_json || workflowState.step4Data.plan || {};
        const saveResponse = await fetch('/api/v1/travel-plans/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                origin: payload.origin,
                destination: payload.destination,
                start_date: payload.start_date,
                days: payload.days,
                travelers: payload.travelers,
                travel_style: payload.travel_style,
                start_location: payload.start_location,
                destination_location: payload.destination_location,
                plan: canonicalPlan,
                costs: workflowState.step4Data.costs || {}
            })
        });

        const saveData = await parseJsonResponse(saveResponse, 'Phản hồi lưu lịch trình không phải JSON hợp lệ.');

        if (saveResponse.ok && saveData.status === 'success') {
            displayStep4Result(workflowState.step4Data);
            showErrorModal('Lịch trình đã được tạo và lưu thành công.', 'success');
            return;
        }

        if (saveResponse.status === 401 || saveResponse.status === 403) {
            displayStep4Result(workflowState.step4Data);
            showErrorModal('Bạn cần đăng nhập để lưu lịch trình này vào tài khoản.');
            return;
        }

        throw new Error(saveData.error || 'Không thể lưu lịch trình vào hệ thống.');
    } catch (error) {
        console.error('Create final plan error:', error);
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = buildSafeFallbackStep4Data(payload, error.message || 'Không thể hoàn thiện lịch trình AI.');
        }
        displayStep4Result(workflowState.step4Data);
        showErrorModal(error.message || 'Không thể hoàn tất lịch trình lúc này. Vui lòng thử lại.');
    } finally {
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalLabel;
        }
    }
}

// Step Navigation
function goToStep(step) {
    // Hide all steps
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Show target step
    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }
    
    // Update progress indicator
    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');
        
        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });
    
    workflowState.currentStep = step;
    
    // Auto-load data for step 3 and 4
    if (step === 3 && !workflowState.step3Data) {
        loadStep3();
    } else if (step === 4 && !workflowState.step4Data) {
        loadStep4();
    }
}

// Helper functions
function formatCurrency(amount) {
    // Format số với dấu phẩy ngăn cách hàng nghìn, không có đơn vị (đã có VND ở nơi gọi)
    return new Intl.NumberFormat('vi-VN').format(Math.round(amount || 0));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatIsoDateForDisplay(isoDate) {
    if (!isoDate || !/^\d{4}-\d{2}-\d{2}$/.test(String(isoDate))) return '';
    const [year, month, day] = String(isoDate).split('-');
    return `${day}/${month}/${year}`;
}

function generateTravelPlanThreadId() {
    const randomPart = Math.random().toString(16).slice(2, 10);
    return `travel-plan-${Date.now()}-${randomPart}`;
}

function resetStreamTrackingState() {
    workflowState.streamedDayKeys = new Set();
    workflowState.streamedProgressKeys = new Set();
}

function registerActiveStream(threadId, payload, mode = 'live') {
    workflowState.activeStream = {
        threadId,
        payload,
        mode,
        eventSource: null,
        status: 'running'
    };
    resetStreamTrackingState();
    persistActiveTravelStream({
        threadId,
        payload,
        mode,
        savedAt: new Date().toISOString()
    });
}

function cleanupActiveStream({ clearStorage = true, clearData = false } = {}) {
    if (workflowState.activeStream?.eventSource) {
        workflowState.activeStream.eventSource.close();
    }

    if (workflowState.postStreamReconnectTimer) {
        window.clearTimeout(workflowState.postStreamReconnectTimer);
        workflowState.postStreamReconnectTimer = null;
    }

    workflowState.activeStream = null;
    resetStreamTrackingState();

    if (clearStorage) {
        clearPersistedTravelStream();
    }

    if (clearData) {
        workflowState.step4Data = null;
    }
}

function hydrateWorkflowStateFromPayload(payload) {
    if (!payload) return;

    const originInput = document.getElementById('origin-input');
    const destinationInput = document.getElementById('destination-input');
    const startDateInput = document.getElementById('start-date');
    const daysInput = document.getElementById('days');
    const travelersInput = document.getElementById('travelers');
    const travelStyleInput = document.getElementById('travel-style');

    if (originInput && payload.origin) {
        originInput.value = payload.origin;
        const [lat, lon] = payload.start_location?.coordinates || [];
        if (Number.isFinite(lat)) originInput.dataset.lat = String(lat);
        if (Number.isFinite(lon)) originInput.dataset.lon = String(lon);
    }

    if (destinationInput && payload.destination) {
        destinationInput.value = payload.destination;
        const [lat, lon] = payload.destination_location?.coordinates || [];
        if (Number.isFinite(lat)) destinationInput.dataset.lat = String(lat);
        if (Number.isFinite(lon)) destinationInput.dataset.lon = String(lon);
    }

    if (startDateInput && payload.start_date) {
        startDateInput.value = formatIsoDateForDisplay(payload.start_date);
    }
    if (daysInput && payload.days) daysInput.value = payload.days;
    if (travelersInput && payload.travelers) travelersInput.value = payload.travelers;
    if (travelStyleInput && payload.travel_style) travelStyleInput.value = payload.travel_style;

    workflowState.step1Data = {
        origin: {
            name: payload.origin,
            latitude: payload.start_location?.coordinates?.[0] ?? null,
            longitude: payload.start_location?.coordinates?.[1] ?? null
        },
        destination: {
            name: payload.destination,
            latitude: payload.destination_location?.coordinates?.[0] ?? null,
            longitude: payload.destination_location?.coordinates?.[1] ?? null
        }
    };

    workflowState.step2Data = {
        start_date: payload.start_date,
        days: payload.days,
        travelers: payload.travelers,
        travel_style: payload.travel_style || 'standard'
    };

    if (payload.selected_hotel) {
        workflowState.step3Data = {
            ...(workflowState.step3Data || {}),
            selected_hotel: payload.selected_hotel
        };
    }
}

function normalizeDateToIso(dateValue) {
    const raw = String(dateValue || '').trim();
    if (!raw) return '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;

    const vnMatch = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (!vnMatch) return raw;

    const [, day, month, year] = vnMatch;
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

function getNumericDatasetValue(element, key, fallbackValue = null) {
    const rawValue = element?.dataset?.[key];
    const numericValue = rawValue === undefined || rawValue === '' ? Number.NaN : Number(rawValue);
    return Number.isFinite(numericValue) ? numericValue : fallbackValue;
}

function buildStep4GenerationPayload() {
    const originInput = document.getElementById('origin-input');
    const destinationInput = document.getElementById('destination-input');
    const startDateInput = document.getElementById('start-date');
    const daysInput = document.getElementById('days');
    const travelersInput = document.getElementById('travelers');
    const travelStyleInput = document.getElementById('travel-style');

    const originName = workflowState.step1Data?.origin?.name || originInput?.value?.trim() || '';
    const destinationName = workflowState.step1Data?.destination?.name || destinationInput?.value?.trim() || '';
    const startDateIso = normalizeDateToIso(workflowState.step2Data?.start_date || startDateInput?.value || '');
    const durationDays = Math.min(14, Math.max(1, Number(workflowState.step2Data?.days || daysInput?.value || 1)));
    const groupSize = Math.min(20, Math.max(1, Number(workflowState.step2Data?.travelers || travelersInput?.value || 1)));
    const travelStyle = workflowState.step2Data?.travel_style || travelStyleInput?.value || 'standard';

    const originLat = getNumericDatasetValue(originInput, 'lat', Number(workflowState.step1Data?.origin?.latitude));
    const originLng = getNumericDatasetValue(originInput, 'lon', Number(workflowState.step1Data?.origin?.longitude));
    const destinationLat = getNumericDatasetValue(destinationInput, 'lat', Number(workflowState.step1Data?.destination?.latitude));
    const destinationLng = getNumericDatasetValue(destinationInput, 'lon', Number(workflowState.step1Data?.destination?.longitude));

    const payload = {
        start_location: {
            name: originName,
            coordinates: [Number.isFinite(originLat) ? originLat : null, Number.isFinite(originLng) ? originLng : null]
        },
        destination_location: {
            name: destinationName,
            coordinates: [Number.isFinite(destinationLat) ? destinationLat : null, Number.isFinite(destinationLng) ? destinationLng : null]
        },
        start_date: startDateIso,
        duration_days: durationDays,
        group_size: groupSize,
        travel_style: travelStyle,
        origin: originName,
        destination: destinationName,
        days: durationDays,
        travelers: groupSize,
        rooms: 1,
        interests: [],
        telemetry_contract_version: 'v1'
    };

    if (workflowState.step3Data?.selected_hotel) {
        payload.selected_hotel = workflowState.step3Data.selected_hotel;
    }

    return payload;
}

async function preflightTravelPlanStream(threadId) {
    const response = await fetch(`/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`, {
        method: 'GET',
        headers: {
            Accept: 'text/event-stream'
        }
    });

    if (!response.ok) {
        let errorPayload = {};
        try {
            errorPayload = await parseJsonResponse(response, 'Không thể khôi phục luồng AI.');
        } catch (error) {
            throw new Error(error.message || 'Không thể khôi phục luồng AI.');
        }
        throw new Error(errorPayload.error || 'Không thể khôi phục luồng AI.');
    }

    if (response.body?.cancel) {
        try {
            await response.body.cancel();
        } catch (error) {
            console.warn('Không thể đóng preflight stream phụ.', error);
        }
    }
}

function connectTravelPlanEventSource(threadId) {
    const streamUrl = `/api/v1/travel-plans/stream/${encodeURIComponent(threadId)}/`;
    const eventSource = new EventSource(streamUrl);

    if (!workflowState.activeStream) {
        workflowState.activeStream = { threadId, eventSource, status: 'running' };
    } else {
        workflowState.activeStream.eventSource = eventSource;
        workflowState.activeStream.status = 'running';
    }

    ['connected', 'progress', 'day_ready', 'completed', 'error'].forEach((eventName) => {
        eventSource.addEventListener(eventName, (event) => {
            let payload = {};
            try {
                payload = event.data ? JSON.parse(event.data) : {};
            } catch (error) {
                console.error('Không thể parse SSE payload:', error, event.data);
            }
            handleStreamEvent(eventName, payload);
        });
    });

    eventSource.onerror = () => {
        if (!workflowState.activeStream || workflowState.activeStream.threadId !== threadId) {
            eventSource.close();
            return;
        }

        eventSource.close();
        workflowState.activeStream.eventSource = null;

        if (workflowState.activeStream.status === 'completed') {
            return;
        }

        appendStreamingProgress('reconnect', 'Luồng SSE bị gián đoạn, đang thử kết nối lại…');
        workflowState.postStreamReconnectTimer = window.setTimeout(() => {
            connectTravelPlanEventSource(threadId);
        }, 1200);
    };
}

function goToStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.remove('active');
    });

    const targetStep = document.getElementById(`step-${step}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    document.querySelectorAll('.step-item').forEach((item, index) => {
        const stepNum = index + 1;
        item.classList.remove('active', 'completed');

        if (stepNum < step) {
            item.classList.add('completed');
        } else if (stepNum === step) {
            item.classList.add('active');
        }
    });

    workflowState.currentStep = step;

    if (step === 3 && !workflowState.step3Data) {
        loadStep3();
    } else if (step === 4 && !workflowState.step4Data && !workflowState.activeStream) {
        loadStep4();
    }
}

async function createFinalPlan() {
    const createBtn = document.getElementById('step4-create');
    const resultDiv = document.getElementById('step4-result');
    const payload = buildStep4GenerationPayload();

    if (!payload.origin || !payload.destination || !payload.start_date) {
        showErrorModal('Thiếu dữ liệu hành trình. Vui lòng kiểm tra lại 4 bước trước khi tạo lịch trình.');
        return;
    }

    if (workflowState.activeStream?.threadId) {
        showErrorModal('Luồng AI hiện tại vẫn đang chạy. Vui lòng chờ hoàn tất hoặc tải lại trang để khôi phục.');
        return;
    }

    const threadId = generateTravelPlanThreadId();
    const originalLabel = createBtn ? createBtn.innerHTML : '';

    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khởi tạo luồng AI...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(payload, threadId);
    }

    try {
        registerActiveStream(threadId, payload, 'live');
        appendStreamingProgress('bootstrap', 'Đã tạo thread_id, đang yêu cầu backend bắt đầu lập lịch trình…');
        await bootstrapTravelPlanStream(payload, threadId);
    } catch (error) {
        console.error('Create final plan stream error:', error);
        cleanupActiveStream({ clearStorage: true, clearData: false });
        if (!workflowState.step4Data?.plan) {
            workflowState.step4Data = buildSafeFallbackStep4Data(
                payload,
                error.message || 'Không thể hoàn thiện lịch trình AI.'
            );
        }
        displayStep4Result(workflowState.step4Data);
        showErrorModal(error.message || 'Không thể hoàn tất lịch trình lúc này. Vui lòng thử lại.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = originalLabel;
        }
    }
}

async function resumeTravelPlanStreamFromStorage() {
    const persisted = loadPersistedTravelStream();
    if (!persisted?.threadId || !persisted?.payload) return;

    hydrateWorkflowStateFromPayload(persisted.payload);
    workflowState.step4Data = workflowState.step4Data || { status: 'streaming' };
    goToStep(4);

    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    if (resultDiv) {
        resultDiv.innerHTML = renderStep4StreamingShell(persisted.payload, persisted.threadId);
    }
    if (createBtn) {
        createBtn.disabled = true;
        createBtn.innerHTML = '<span class="loading-spinner"></span> Đang khôi phục luồng AI...';
    }

    registerActiveStream(persisted.threadId, persisted.payload, 'resume');
    appendStreamingProgress('resume', 'Đã tìm thấy thread_id trước đó, đang phát lại tiến độ…');

    try {
        await preflightTravelPlanStream(persisted.threadId);
    } catch (error) {
        cleanupActiveStream({ clearStorage: true, clearData: true });
        showErrorModal(error.message || 'Không thể khôi phục luồng AI.');
        if (createBtn) {
            createBtn.disabled = false;
            createBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Tạo lịch trình';
        }
        return;
    }

    connectTravelPlanEventSource(persisted.threadId);
}

window.goToStep = goToStep;
window.createFinalPlan = createFinalPlan;
window.closeErrorModal = closeErrorModal;

document.addEventListener('DOMContentLoaded', () => {
    const step4Header = document.querySelector('#step-4 .step-header h2');
    const step4Intro = document.querySelector('#step-4 .step-header p');
    const step4Notice = document.querySelector('#step-4 .tp-soft');
    const modalTitle = document.querySelector('#error-modal-overlay .error-modal-header h3');
    const modalButton = document.querySelector('#error-modal-overlay .error-modal-btn');

    if (step4Header) {
        step4Header.textContent = 'Rà soát blueprint chuyến đi trước khi hoàn tất';
    }
    if (step4Intro) {
        step4Intro.textContent = 'Xem lại tổng chi phí, hoạt động gợi ý và timeline từng ngày. Khi bạn bấm tạo lịch trình, Atlas sẽ phát tiến độ theo thời gian thực và tự khôi phục nếu trang bị tải lại giữa chừng.';
    }
    if (step4Notice) {
        step4Notice.innerHTML = '<strong class="text-slate-900 dark:text-slate-100">Lưu ý chính xác:</strong> Nút <em>Tạo lịch trình</em> sẽ mở luồng AI theo thời gian thực, phát từng ngày khi sẵn sàng và đồng bộ với trạng thái lưu lịch trình ở backend.';
    }
    if (modalTitle) {
        modalTitle.textContent = 'Thông báo';
    }
    if (modalButton) {
        modalButton.textContent = 'Đã hiểu';
    }
});

function renderStep4LoadingState(title = 'Atlas đang dựng blueprint', subtitle = 'Lịch trình tổng quan đang được ghép từ hoạt động, chi phí và gợi ý di chuyển.') {
    return `
        <div class="step4-shell animate-pulse">
            ${renderStepPanel({
                icon: 'fa-solid fa-road',
                title,
                subtitle,
                content: '<div class="loading-line lg"></div><div class="loading-line md" style="margin-top:0.85rem;"></div><div class="loading-line sm" style="margin-top:0.85rem;"></div>'
            })}
        </div>
    `;
}

async function parseJsonResponse(response, defaultErrorMessage = 'Phản hồi từ hệ thống AI không hợp lệ.') {
    const rawText = await response.text();
    if (!rawText.trim()) {
        return {};
    }

    try {
        return JSON.parse(rawText);
    } catch (error) {
        console.error('JSON parse error:', error, rawText);
        throw new Error(defaultErrorMessage);
    }
}

function buildSafeFallbackStep4Data(payload, reason = 'Atlas chưa trả về JSON hoàn chỉnh nên hệ thống dùng blueprint an toàn để bạn tiếp tục.') {
    const totalDays = Math.max(1, Number(payload.duration_days || 1));
    const destinationName = payload.destination_location?.name || payload.destination || 'Điểm đến';
    const originName = payload.start_location?.name || payload.origin || 'Điểm đi';
    const travelStyle = payload.travel_style || 'standard';
    const budget = workflowState.step3Data?.budget || {};
    const breakdown = budget.breakdown || {};
    const total = Number(budget.total_vnd || 0);

    const startDate = payload.start_date || normalizeDateToIso(document.getElementById('start-date')?.value || '');
    const dailyPlans = Array.from({ length: totalDays }, (_, index) => {
        const currentDate = new Date(startDate || new Date().toISOString().slice(0, 10));
        if (!Number.isNaN(currentDate.getTime())) {
            currentDate.setDate(currentDate.getDate() + index);
        }

        return {
            day: index + 1,
            date: Number.isNaN(currentDate.getTime()) ? '' : currentDate.toISOString().slice(0, 10),
            theme: index === 0 ? 'Khởi động hành trình' : `Khám phá ${destinationName}`,
            activities: [
                {
                    time: 'Sáng',
                    activity: { name: `Di chuyển từ ${originName} đến ${destinationName}` },
                    description: 'Ưu tiên kiểm tra thời tiết, nhận phòng và chốt tuyến tham quan gần nhau để hành trình mượt hơn.'
                },
                {
                    time: 'Chiều',
                    activity: { name: `Khám phá các điểm nổi bật phù hợp phong cách ${travelStyle}` },
                    description: 'Đây là lịch trình an toàn tạm thời để bạn có thể tiếp tục thao tác khi phản hồi AI chính chưa sẵn sàng.'
                },
                {
                    time: 'Tối',
                    activity: { name: `Thưởng thức ẩm thực địa phương tại ${destinationName}` },
                    description: 'Nên ưu tiên khu vực trung tâm hoặc gần nơi lưu trú để tối ưu thời gian di chuyển.'
                }
            ],
            meals: {
                lunch: `Bữa trưa gợi ý tại ${destinationName}`,
                dinner: `Bữa tối đặc trưng tại ${destinationName}`
            },
            tips: [
                reason,
                'Bạn vẫn có thể lưu lịch trình này hoặc thử tạo lại để nhận phiên bản AI đầy đủ hơn.'
            ]
        };
    });

    return {
        status: 'success',
        is_fallback: true,
        fallback_reason: reason,
        plan: {
            transport: workflowState.step2Data?.transport || {},
            selected_hotel: workflowState.step3Data?.selected_hotel || null,
            hotels: workflowState.step3Data?.hotels || [],
            activities: [],
            restaurants: [],
            budget: budget,
            itinerary: {
                destination: destinationName,
                total_days: totalDays,
                daily_plans: dailyPlans
            },
            itinerary_json: {
                destination: destinationName,
                travel_style: travelStyle,
                daily_plans: dailyPlans
            },
            itinerary_description: reason
        },
        costs: {
            transport: Number(breakdown.transport || 0),
            accommodation: Number(breakdown.accommodation || 0),
            activities: Number(breakdown.activities || 0),
            dining: Number(breakdown.dining || 0),
            total
        }
    };
}

async function requestStep4Plan(payload) {
    const response = await fetch('/api/v1/travel-plans/step4/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    });

    let data;
    try {
        data = await parseJsonResponse(response, 'Phản hồi từ bộ tạo lịch trình không phải JSON hợp lệ.');
    } catch (error) {
        return buildSafeFallbackStep4Data(payload, error.message);
    }

    if (response.ok && data.status === 'success') {
        return data;
    }

    const errorMessage = data?.error || 'Không thể tạo lịch trình tổng quan.';
    console.error('Step 4 API error:', errorMessage, data);
    return buildSafeFallbackStep4Data(payload, errorMessage);
}

// Load travel styles from API
async function loadTravelStyles() {
    const travelStyleSelect = document.getElementById('travel-style');
    const smallText = travelStyleSelect ? travelStyleSelect.parentElement.querySelector('small') : null;
    
    if (!travelStyleSelect) return;
    
    try {
        const response = await fetch('/api/v1/travel-styles/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.styles) {
            // Clear existing options (except default)
            travelStyleSelect.innerHTML = '';
            
            // Style icons mapping
            const styleIcons = {
                'budget': '💰',
                'standard': '⭐',
                'luxury': '✨',
                'adventure': '🏔️',
                'cultural': '🏛️',
                'gastronomy': '🍽️',
                'eco': '🌱',
                'wellness': '🧘',
                'family': '👨‍👩‍👧‍👦',
                'romantic': '💕',
                'slow': '🐌',
                'digital_nomad': '💻',
                'shop_leisure': '🛍️',
                'photography': '📸',
                'religious': '🕉️',
                'festival': '🎉',
                'extreme': '⚡'
            };
            
            // Group styles: Core first, then extended
            const coreStyles = ['budget', 'standard', 'luxury'];
            const extendedStyles = data.styles.filter(s => !coreStyles.includes(s.value));
            
            // Add core styles first
            coreStyles.forEach(value => {
                const style = data.styles.find(s => s.value === value);
                if (style) {
                    const option = document.createElement('option');
                    option.value = style.value;
                    option.textContent = `${styleIcons[style.value] || '⭐'} ${style.name}`;
                    if (style.value === 'standard') option.selected = true;
                    travelStyleSelect.appendChild(option);
                }
            });
            
            // Add separator
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '───────────';
            travelStyleSelect.appendChild(separator);
            
            // Add extended styles
            extendedStyles.forEach(style => {
                const option = document.createElement('option');
                option.value = style.value;
                option.textContent = `${styleIcons[style.value] || '⭐'} ${style.name}`;
                travelStyleSelect.appendChild(option);
            });
            
            // Hide loading text
            if (smallText) {
                smallText.style.display = 'none';
            }

            travelStyleSelect.dispatchEvent(new Event('travel-styles:loaded', { bubbles: true }));
            travelStyleSelect.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            // Fallback to basic styles if API fails
            if (smallText) {
                smallText.textContent = 'Sử dụng phong cách cơ bản';
                smallText.style.color = 'var(--color-gray-500)';
            }
        }
    } catch (error) {
        console.error('Error loading travel styles:', error);
        // Fallback to basic styles
        if (smallText) {
            smallText.textContent = 'Sử dụng phong cách cơ bản';
            smallText.style.color = 'var(--color-gray-500)';
        }
    }
}

// Export functions for use in HTML
window.goToStep = goToStep;
window.selectHotel = selectHotel;
window.createFinalPlan = createFinalPlan;
window.toggleDay = toggleDay;

// Override Step 1 interactions with cleaner map behavior and Vietnam-only bounds.
async function handleCurrentLocation() {
    const btn = document.getElementById('use-current-location-btn');
    const statusSpan = document.getElementById('location-status');
    const originInput = document.getElementById('origin-input');
    const chip = document.getElementById('detected-chip');
    const addressSpan = document.getElementById('detected-address');

    if (!btn || !originInput || !statusSpan || isResolvingCurrentLocation) return;

    isResolvingCurrentLocation = true;

    btn.disabled = true;
    const btnText = btn.querySelector('.btn-text');
    const originalBtnText = btnText ? btnText.textContent : 'Dùng vị trí hiện tại';
    if (btnText) btnText.textContent = 'Đang xác định vị trí...';
    statusSpan.textContent = 'Trình duyệt sẽ yêu cầu quyền truy cập vị trí để dùng điểm đi hiện tại.';
    statusSpan.style.color = '#475569';

    try {
        if (!navigator.geolocation) {
            throw new Error('Trình duyệt không hỗ trợ định vị. Vui lòng nhập thủ công.');
        }

        navigator.geolocation.getCurrentPosition(async (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const accuracy = position.coords.accuracy || 0;

            try {
                const response = await fetch(`/api/v1/locations/reverse-geocode/?lat=${lat}&lon=${lon}`);
                const data = await response.json();

                let displayAddress = '';
                if (data.status === 'success' && data.address) {
                    displayAddress = data.address;
                } else if (data.location) {
                    displayAddress = data.location;
                } else {
                    displayAddress = `Vị trí (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
                }

                const accuracyText = accuracy > 0 ? ` • ±${Math.round(accuracy)}m` : '';
                if (addressSpan) {
                    addressSpan.textContent = `${displayAddress}${accuracyText}`;
                }
                if (chip) {
                    chip.classList.remove('hidden');
                }

                originInput.dataset.lat = String(lat);
                originInput.dataset.lon = String(lon);

                const destinationInput = document.getElementById('destination-input');
                const destinationLat = Number(destinationInput?.dataset.lat);
                const destinationLon = Number(destinationInput?.dataset.lon);
                const hasDestinationGeo = Number.isFinite(destinationLat) && Number.isFinite(destinationLon);

                updateOriginMap(lat, lon, {
                    accuracy,
                    originLabel: displayAddress,
                    destination: hasDestinationGeo ? {
                        lat: destinationLat,
                        lon: destinationLon,
                        label: destinationInput?.value || 'Điểm đến'
                    } : null
                });

                statusSpan.textContent = 'Đã lấy vị trí hiện tại. Bạn có thể xác nhận để dùng làm điểm đi.';
                statusSpan.style.color = '#0f766e';
            } catch (error) {
                console.error('Error in reverse geocoding:', error);
                statusSpan.textContent = 'Không thể tra địa chỉ từ vị trí hiện tại. Vui lòng thử lại.';
                statusSpan.style.color = '#dc2626';
            } finally {
                isResolvingCurrentLocation = false;
                btn.disabled = false;
                if (btnText) btnText.textContent = originalBtnText;
            }
        }, (error) => {
            console.error('Geolocation error:', error);
            let errorMessage = 'Không thể xác định vị trí.';
            if (error.code === 1) {
                errorMessage = 'Bạn đã từ chối quyền truy cập vị trí. Vui lòng cho phép hoặc nhập thủ công.';
            } else if (error.code === 2) {
                errorMessage = 'Không thể xác định vị trí. Vui lòng kiểm tra kết nối hoặc GPS.';
            } else if (error.code === 3) {
                errorMessage = 'Hết thời gian chờ khi lấy vị trí hiện tại.';
            }

            statusSpan.textContent = errorMessage;
            statusSpan.style.color = '#dc2626';
            isResolvingCurrentLocation = false;
            btn.disabled = false;
            if (btnText) btnText.textContent = originalBtnText;
            originInput.focus();
        }, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
        });
    } catch (error) {
        console.error('Error in handleCurrentLocation:', error);
        statusSpan.textContent = `Đã xảy ra lỗi: ${error.message}`;
        statusSpan.style.color = '#dc2626';
        isResolvingCurrentLocation = false;
        btn.disabled = false;
        if (btnText) btnText.textContent = originalBtnText;
    }
}

async function handleStep1Submit(e) {
    e.preventDefault();

    const originInput = document.getElementById('origin-input');
    const destinationInput = document.getElementById('destination-input');

    const origin = originInput ? originInput.value.trim() : '';
    const destination = destinationInput ? destinationInput.value.trim() : '';

    if (!origin || origin.length < 2) {
        showError('Vui lòng nhập điểm xuất phát (ít nhất 2 ký tự).');
        if (originInput) originInput.focus();
        return;
    }

    if (!destination || destination.length < 2) {
        showError('Vui lòng nhập điểm đến (ít nhất 2 ký tự).');
        if (destinationInput) destinationInput.focus();
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : 'Tiếp tục';
    const resultDiv = document.getElementById('step1-result');

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Đang kiểm tra...';
    }

    if (resultDiv) {
        resultDiv.innerHTML = '';
        resultDiv.style.display = 'none';
    }

    try {
        const response = await fetch('/api/v1/travel-plans/step1/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                origin,
                destination
            })
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            if (originInput && data.origin) {
                if ((!originInput.dataset.lat || originInput.dataset.lat === '') && data.origin.latitude !== undefined && data.origin.latitude !== null) {
                    originInput.dataset.lat = String(data.origin.latitude);
                }
                if ((!originInput.dataset.lon || originInput.dataset.lon === '') && data.origin.longitude !== undefined && data.origin.longitude !== null) {
                    originInput.dataset.lon = String(data.origin.longitude);
                }
            }

            if (destinationInput && data.destination) {
                destinationInput.dataset.lat = data.destination.latitude ?? '';
                destinationInput.dataset.lon = data.destination.longitude ?? '';
            }

            workflowState.step1Data = data;
            displayStep1Result(data);
            updateRoutePreviewMap(data);

            setTimeout(() => {
                goToStep(2);
            }, 1000);
        } else {
            const errorMsg = data.error || 'Không thể xử lý yêu cầu.';
            showError(errorMsg);

            if (data.origin && !data.destination) {
                if (destinationInput) destinationInput.style.borderColor = '#dc2626';
            } else if (data.destination && !data.origin) {
                if (originInput) originInput.style.borderColor = '#dc2626';
            } else {
                if (originInput) originInput.style.borderColor = '#dc2626';
                if (destinationInput) destinationInput.style.borderColor = '#dc2626';
            }
        }
    } catch (error) {
        console.error('Step 1 error:', error);
        showError('Lỗi kết nối. Vui lòng kiểm tra kết nối mạng và thử lại.');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }
}


