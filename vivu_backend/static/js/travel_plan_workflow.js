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
    step4Data: null
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWorkflow();
    loadTravelStyles(); // Load travel styles from API
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

// Current location handler with mini-map
async function handleCurrentLocation() {
    const btn = document.getElementById('use-current-location-btn');
    const statusSpan = document.getElementById('location-status');
    const originInput = document.getElementById('origin-input');
    const chip = document.getElementById('detected-chip');
    const addressSpan = document.getElementById('detected-address');
    const miniMap = document.getElementById('origin-mini-map');
    
    if (!btn || !originInput || !statusSpan) return;
    
    // Update button state
    btn.disabled = true;
    const btnText = btn.querySelector('.btn-text');
    const originalBtnText = btnText.textContent;
    btnText.textContent = 'Đang xác định vị trí...';
    statusSpan.textContent = '';
    
    try {
        if (!navigator.geolocation) {
            throw new Error('Trình duyệt không hỗ trợ vị trí. Vui lòng nhập thủ công.');
        }
        
        navigator.geolocation.getCurrentPosition(async (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const accuracy = position.coords.accuracy || 0;
            
            try {
                // Reverse geocode
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
                
                // Show chip with address and accuracy
                const accuracyText = accuracy > 0 ? ` • ±${Math.round(accuracy)}m` : '';
                if (addressSpan) {
                    addressSpan.textContent = `${displayAddress}${accuracyText}`;
                }
                if (chip) {
                    chip.classList.remove('hidden');
                }
                
                // Store coordinates in a hidden way (can be used for API calls)
                originInput.dataset.lat = lat;
                originInput.dataset.lon = lon;
                
                // Show mini map
                if (miniMap) {
                    miniMap.classList.remove('hidden');
                    miniMap.classList.add('visible');
                    miniMap.setAttribute('aria-hidden', 'false');
                    
                    // Initialize or update map
                    if (!originMap) {
                        originMap = L.map('origin-mini-map', {
                            zoomControl: true,
                            scrollWheelZoom: true,
                            doubleClickZoom: true,
                            touchZoom: true,
                            boxZoom: false,
                            dragging: true
                        }).setView([lat, lon], accuracy > 100 ? 13 : 15);
                        
                        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                            attribution: '© OpenStreetMap contributors',
                            maxZoom: 19
                        }).addTo(originMap);
                        
                        // Create marker with accuracy circle
                        originMarker = L.marker([lat, lon]).addTo(originMap);
                        
                        if (accuracy > 0) {
                            L.circle([lat, lon], {
                                radius: accuracy,
                                color: 'var(--color-secondary)',
                                fillColor: 'var(--color-secondary)',
                                fillOpacity: 0.2,
                                weight: 2
                            }).addTo(originMap);
                        }
                    } else {
                        originMap.setView([lat, lon], accuracy > 100 ? 13 : 15);
                        if (originMarker) {
                            originMarker.setLatLng([lat, lon]);
                        }
                    }
                    
                    // Ensure map is properly sized after showing
                    setTimeout(() => {
                        if (originMap) {
                            originMap.invalidateSize();
                        }
                    }, 100);
                }
                
                // Update status
                statusSpan.textContent = 'Vị trí đã được phát hiện';
                statusSpan.style.color = 'var(--color-secondary-dark)';
                
                // Don't auto-fill input - let user confirm first
                // originInput.value = displayAddress;
                
            } catch (error) {
                console.error('Error in reverse geocoding:', error);
                statusSpan.textContent = 'Không thể tra địa chỉ. Vui lòng thử lại.';
                statusSpan.style.color = '#dc2626';
            } finally {
                btn.disabled = false;
                btnText.textContent = originalBtnText;
            }
        }, (error) => {
            console.error('Geolocation error:', error);
            let errorMessage = 'Không thể xác định vị trí.';
            if (error.code === 1) {
                errorMessage = 'Bạn đã từ chối quyền truy cập vị trí. Vui lòng nhập thủ công.';
            } else if (error.code === 2) {
                errorMessage = 'Không thể xác định vị trí. Vui lòng kiểm tra kết nối.';
            } else if (error.code === 3) {
                errorMessage = 'Hết thời gian chờ khi lấy vị trí.';
            }
            
            statusSpan.textContent = errorMessage;
            statusSpan.style.color = '#dc2626';
            btn.disabled = false;
            btnText.textContent = originalBtnText;
            
            // Focus on input for manual entry
            if (originInput) {
                originInput.focus();
            }
        }, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000 // Cache for 1 minute
        });
    } catch (error) {
        console.error('Error in handleCurrentLocation:', error);
        statusSpan.textContent = 'Đã xảy ra lỗi: ' + error.message;
        statusSpan.style.color = '#dc2626';
        btn.disabled = false;
        btnText.textContent = originalBtnText;
    }
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
            // Không tự động chuyển sang Step 3, đợi user chọn phương tiện và click "Tiếp tục"
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
    const distance_km = transport.distance_km || 0;
    const cheapest = transport.cheapest || null;
    const fastest = transport.fastest || null;
    
    // Tạo danh sách phương tiện để user chọn
    let optionsHTML = '';
    if (options.length > 0) {
        optionsHTML = '<div class="transport-options" style="display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem;">';
        options.forEach((opt, index) => {
            const method = opt.method || '';
            const methodName = opt.method_name || opt.name || method;
            // Tính cost: nếu có cost_vnd thì dùng, nếu không thì tính từ cost_per_person
            let cost = opt.cost_vnd || 0;
            if (cost === 0 && opt.cost_per_person) {
                cost = opt.cost_per_person * (workflowState.step2Data.travelers || 1);
            }
            const duration = opt.duration_minutes || 0;
            const hours = Math.floor(duration / 60);
            const minutes = duration % 60;
            const durationText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
            
            // Icon mapping
            const iconMap = {
                'flight': '✈️',
                'train': '🚂',
                'long_distance_bus': '🚌',
                'city_bus': '🚌',
                'taxi': '🚕',
                'grab': '🚗',
                'gojek': '🏍️',
                'be': '🏍️',
                'motorbike': '🏍️',
                'car': '🚗',
                'greencar': '🚗',
                'luxurycar': '🚗',
                'walking': '🚶',
                'bicycle': '🚴'
            };
            const icon = iconMap[method] || '🚗';
            
            // Check if this is the cheapest or fastest
            const isCheapest = cheapest && cheapest.method === method;
            const isFastest = fastest && fastest.method === method;
            
            optionsHTML += `
                <div class="transport-option" data-method="${method}" data-index="${index}" 
                     onclick="selectTransport('${method}', ${index})" 
                     style="padding: 1rem; border: 2px solid #e0e0e0; border-radius: 8px; cursor: pointer; transition: all 0.3s; background: white;"
                     onmouseover="this.style.borderColor='var(--color-secondary)'" 
                     onmouseout="if(!this.classList.contains('selected')) this.style.borderColor='#e0e0e0'">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem;">${icon}</div>
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <strong style="font-size: 1.1rem; color: var(--color-primary-dark);">${methodName}</strong>
                                ${isCheapest ? '<span style="background: #4CAF50; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">Rẻ nhất</span>' : ''}
                                ${isFastest ? '<span style="background: #2196F3; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">Nhanh nhất</span>' : ''}
                            </div>
                            <div style="margin-top: 0.5rem; color: var(--color-gray-600);">
                                <span>⏱️ ${durationText}</span>
                                <span style="margin-left: 1rem;">💰 ${formatCurrency(cost)} VNĐ</span>
                                ${opt.cost_per_person ? `<span style="margin-left: 1rem; font-size: 0.9rem;">(${formatCurrency(opt.cost_per_person)} VNĐ/người)</span>` : ''}
                            </div>
                            ${opt.description ? `<div style="margin-top: 0.25rem; font-size: 0.85rem; color: var(--color-gray-500);">${opt.description}</div>` : ''}
                        </div>
                        <div class="transport-radio" style="width: 24px; height: 24px; border: 2px solid #ccc; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                            <div style="width: 12px; height: 12px; background: var(--color-secondary); border-radius: 50%; display: none;"></div>
                        </div>
                    </div>
                </div>
            `;
        });
        optionsHTML += '</div>';
    }
    
    // Hiển thị thông báo nếu không có phương tiện
    if (options.length === 0) {
        resultDiv.innerHTML = `
            <div class="info-card" style="margin-top: 1.5rem; padding: 2rem; text-align: center;">
                <h4>⚠️ Không tìm thấy phương tiện phù hợp</h4>
                <p style="color: var(--color-gray-600); margin-top: 1rem;">
                    Không thể tìm thấy phương tiện di chuyển cho tuyến đường này. 
                    Vui lòng thử lại hoặc chọn điểm đến khác.
                </p>
            </div>
        `;
        resultDiv.style.display = 'block';
        return;
    }
    
    resultDiv.innerHTML = `
        <div class="info-card" style="margin-top: 1.5rem;">
            <h4>✈️ Chọn phương tiện di chuyển</h4>
            <p style="margin-bottom: 0.5rem;"><strong>Khoảng cách:</strong> ${distance_km.toFixed(1)} km</p>
            <p style="margin-bottom: 1rem;"><strong>Phương tiện đề xuất:</strong> ${data.recommended_transport || 'Nhiều lựa chọn'}</p>
            ${optionsHTML}
        </div>
        <div class="info-card" style="margin-top: 1rem;">
            <h4>📅 Thông tin chuyến đi</h4>
            <p><strong>Số ngày:</strong> ${data.recommended_days || workflowState.step2Data.days} ngày</p>
            <p><strong>Số người:</strong> ${workflowState.step2Data.travelers} người</p>
        </div>
        <div style="margin-top: 1.5rem; text-align: center;">
            <button type="button" class="btn-workflow btn-primary" id="step2-continue" onclick="continueToStep3()" disabled>
                Tiếp tục
            </button>
        </div>
    `;
    resultDiv.style.display = 'block';
}

function selectTransport(method, index) {
    // Remove previous selection
    document.querySelectorAll('.transport-option').forEach(opt => {
        opt.classList.remove('selected');
        opt.style.borderColor = '#e0e0e0';
        opt.style.backgroundColor = 'white';
        const radio = opt.querySelector('.transport-radio > div');
        if (radio) radio.style.display = 'none';
    });
    
    // Mark as selected - use data-index for more reliable selection
    const selectedOption = document.querySelector(`.transport-option[data-index="${index}"]`);
    
    if (selectedOption) {
        selectedOption.classList.add('selected');
        selectedOption.style.borderColor = 'var(--color-secondary)';
        selectedOption.style.backgroundColor = 'rgba(var(--color-secondary-rgb), 0.05)';
        const radio = selectedOption.querySelector('.transport-radio > div');
        if (radio) radio.style.display = 'block';
        
        // Save selected transport to state
        const transport = workflowState.step2Data.transport || {};
        const options = transport.options || [];
        
        if (options && options.length > index && options[index]) {
            workflowState.step2Data.selected_transport = options[index];
        }
        
        // Enable continue button
        const continueBtn = document.getElementById('step2-continue');
        if (continueBtn) {
            continueBtn.disabled = false;
        }
    }
}

function continueToStep3() {
    if (!workflowState.step2Data.selected_transport) {
        showErrorModal('Vui lòng chọn phương tiện di chuyển');
        return;
    }
    
    // Proceed to Step 3
    goToStep(3);
    loadStep3();
}

// Step 3: Budget & Hotels
async function loadStep3() {
    const resultDiv = document.getElementById('step3-result');
    const continueBtn = document.getElementById('step3-continue');
    
    if (!resultDiv) return;
    
    resultDiv.innerHTML = '<div style="text-align: center; padding: 3rem;"><p>Đang tải thông tin...</p></div>';
    
    try {
        const payload = {
            origin: workflowState.step1Data.origin.name,
            destination: workflowState.step1Data.destination.name,
            start_date: workflowState.step2Data.start_date,
            days: workflowState.step2Data.days,
            travelers: workflowState.step2Data.travelers,
            travel_style: workflowState.step2Data.travel_style,
            rooms: 1
        };
        
        // Include selected transport if available
        if (workflowState.step2Data.selected_transport) {
            payload.selected_transport = workflowState.step2Data.selected_transport;
        }
        
        const response = await fetch('/api/v1/travel-plans/step3/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            workflowState.step3Data = data;
            displayStep3Result(data);
            // Button "Tiếp tục" sẽ được enable khi user chọn khách sạn
            if (continueBtn) continueBtn.disabled = true;
        } else {
            resultDiv.innerHTML = `<div style="color: red; padding: 2rem;">Lỗi: ${data.error || 'Không thể tải dữ liệu'}</div>`;
        }
    } catch (error) {
        console.error('Step 3 error:', error);
        resultDiv.innerHTML = '<div style="color: red; padding: 2rem;">Lỗi kết nối. Vui lòng thử lại.</div>';
    }
}

function displayStep3Result(data) {
    const resultDiv = document.getElementById('step3-result');
    if (!resultDiv) return;
    
    const budget = data.budget || {};
    const breakdown = budget.breakdown || {};
    const hotels = data.hotels || [];
    
    let budgetHTML = '';
    if (budget.total_vnd) {
        budgetHTML = `
            <div class="budget-breakdown">
                <h4>💰 Phân tích ngân sách</h4>
                <div class="budget-item">
                    <span>Di chuyển</span>
                    <span>${formatCurrency(breakdown.transport || 0)} VNĐ</span>
                </div>
                <div class="budget-item">
                    <span>Lưu trú</span>
                    <span>${formatCurrency(breakdown.accommodation || 0)} VNĐ</span>
                </div>
                <div class="budget-item">
                    <span>Ăn uống</span>
                    <span>${formatCurrency(breakdown.dining || 0)} VNĐ</span>
                </div>
                <div class="budget-item">
                    <span>Hoạt động</span>
                    <span>${formatCurrency(breakdown.activities || 0)} VNĐ</span>
                </div>
                <div class="budget-item">
                    <span>Tổng cộng</span>
                    <span>${formatCurrency(budget.total_vnd)} VNĐ</span>
                </div>
                <div class="budget-summary-footer">
                    <p>
                        <strong>/người:</strong> ${formatCurrency(budget.per_person || 0)} VNĐ
                        <span style="margin-left: 1rem;">
                            <strong>/ngày:</strong> ${formatCurrency(budget.per_day || 0)} VNĐ
                        </span>
                    </p>
                </div>
            </div>
        `;
    }
    
    let hotelsHTML = '';
    if (hotels.length > 0) {
        hotelsHTML = `
            <div style="margin-top: 2rem;">
                <h4 style="margin-bottom: 1rem; color: var(--color-primary-dark);">🏨 Chọn khách sạn</h4>
                <div class="hotels-list">
                    ${hotels.map((hotel, index) => {
                        // Lấy ảnh đầu tiên nếu có
                        let imageUrl = '';
                        if (hotel.images && hotel.images.length > 0) {
                            imageUrl = hotel.images[0];
                        } else if (hotel.image_url) {
                            imageUrl = hotel.image_url;
                        } else if (hotel.thumbnail) {
                            imageUrl = hotel.thumbnail;
                        }
                        
                        return `
                        <div class="hotel-card" onclick="selectHotel(${index})" data-hotel-index="${index}" 
                             style="padding: 1rem; border: 2px solid #e0e0e0; border-radius: 8px; cursor: pointer; transition: all 0.3s; background: white; margin-bottom: 1rem;"
                             onmouseover="if(!this.classList.contains('selected')) this.style.borderColor='var(--color-secondary)'" 
                             onmouseout="if(!this.classList.contains('selected')) this.style.borderColor='#e0e0e0'">
                            <div style="display: flex; gap: 1.5rem; align-items: flex-start;">
                                ${imageUrl ? `
                                <div style="flex-shrink: 0; width: 150px; height: 120px; border-radius: 8px; overflow: hidden;">
                                    <img src="${imageUrl}" alt="${hotel.name || 'Hotel'}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.style.display='none'">
                                </div>
                                ` : ''}
                                <div style="flex: 1; min-width: 0;">
                                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                        <div class="hotel-name" style="font-size: 1.1rem; font-weight: 600; color: var(--color-primary-dark);">${hotel.name || 'N/A'}</div>
                                        <div class="hotel-radio" style="width: 24px; height: 24px; border: 2px solid #ccc; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-left: auto; flex-shrink: 0;">
                                            <div style="width: 12px; height: 12px; background: var(--color-secondary); border-radius: 50%; display: none;"></div>
                                        </div>
                                    </div>
                                    ${hotel.stars ? `<div class="hotel-rating" style="margin-bottom: 0.5rem;">${'⭐'.repeat(hotel.stars)} ${hotel.rating || ''}/5 ${hotel.reviews ? `(${hotel.reviews} đánh giá)` : ''}</div>` : ''}
                                    ${hotel.hotel_class ? `<div style="font-size: 0.9rem; color: var(--color-gray-600); margin-bottom: 0.5rem;">${hotel.hotel_class} sao</div>` : ''}
                                    ${hotel.address ? `<div style="font-size: 0.9rem; color: var(--color-gray-600); margin-bottom: 0.5rem;">📍 ${hotel.address}</div>` : ''}
                                    ${hotel.phone ? `<div style="font-size: 0.9rem; color: var(--color-gray-600); margin-bottom: 0.25rem;">📞 ${hotel.phone}</div>` : ''}
                                    ${hotel.email ? `<div style="font-size: 0.9rem; color: var(--color-gray-600); margin-bottom: 0.25rem;">✉️ ${hotel.email}</div>` : ''}
                                    ${hotel.website ? `<div style="font-size: 0.9rem; color: var(--color-secondary); margin-bottom: 0.25rem;"><a href="${hotel.website}" target="_blank" onclick="event.stopPropagation();" style="color: var(--color-secondary); text-decoration: none;">🌐 Website</a></div>` : ''}
                                    ${hotel.description ? `<div style="font-size: 0.85rem; color: var(--color-gray-600); margin-top: 0.5rem; line-height: 1.4;">${hotel.description.substring(0, 150)}${hotel.description.length > 150 ? '...' : ''}</div>` : ''}
                                    ${hotel.amenities && hotel.amenities.length > 0 ? `<div style="font-size: 0.85rem; color: var(--color-gray-600); margin-top: 0.5rem; display: flex; flex-wrap: wrap; gap: 0.5rem;">${hotel.amenities.slice(0, 5).map(a => `<span style="background: var(--color-gray-100); padding: 0.25rem 0.5rem; border-radius: 4px;">${a}</span>`).join('')}</div>` : ''}
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
                                        ${hotel.price_per_night ? `<div class="hotel-price" style="font-size: 1.1rem; font-weight: 600; color: var(--color-secondary-dark);">${formatCurrency(hotel.price_per_night)} VNĐ/đêm</div>` : ''}
                                        ${hotel.source ? `<div style="font-size: 0.85rem; color: var(--color-gray-600);">Nguồn: ${hotel.source}</div>` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    resultDiv.innerHTML = budgetHTML + hotelsHTML;
}

function selectHotel(index) {
    // Remove previous selection
    document.querySelectorAll('.hotel-card').forEach(card => {
        card.classList.remove('selected');
        card.style.borderColor = '#e0e0e0';
        card.style.backgroundColor = 'white';
        const radio = card.querySelector('.hotel-radio > div');
        if (radio) radio.style.display = 'none';
    });
    
    // Mark as selected
    const card = document.querySelector(`[data-hotel-index="${index}"]`);
    if (card) {
        card.classList.add('selected');
        card.style.borderColor = 'var(--color-secondary)';
        card.style.backgroundColor = 'rgba(var(--color-secondary-rgb), 0.05)';
        const radio = card.querySelector('.hotel-radio > div');
        if (radio) radio.style.display = 'block';
        
        // Save selected hotel to state
        workflowState.step3Data.selected_hotel = workflowState.step3Data.hotels[index];
        
        // Enable continue button
        const continueBtn = document.getElementById('step3-continue');
        if (continueBtn) {
            continueBtn.disabled = false;
        }
    }
}

function continueToStep4() {
    if (!workflowState.step3Data || !workflowState.step3Data.selected_hotel) {
        showErrorModal('Vui lòng chọn khách sạn');
        return;
    }
    
    // Proceed to Step 4
    goToStep(4);
    loadStep4();
}

// Step 4: Confirm & Create Plan
async function loadStep4() {
    const resultDiv = document.getElementById('step4-result');
    const createBtn = document.getElementById('step4-create');
    
    if (!resultDiv) return;
    
    resultDiv.innerHTML = '<div style="text-align: center; padding: 3rem;"><p style="color: #00838F; font-size: 1.1rem; font-weight: 500;">Đang tạo lịch trình...</p></div>';
    
    try {
        const payload = {
            origin: workflowState.step1Data.origin.name,
            destination: workflowState.step1Data.destination.name,
            start_date: workflowState.step2Data.start_date,
            days: workflowState.step2Data.days,
            travelers: workflowState.step2Data.travelers,
            travel_style: workflowState.step2Data.travel_style,
            rooms: 1,
            interests: []
        };
        
        if (workflowState.step3Data && workflowState.step3Data.selected_hotel) {
            payload.selected_hotel = workflowState.step3Data.selected_hotel;
        }
        
        const response = await fetch('/api/v1/travel-plans/step4/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            workflowState.step4Data = data;
            displayStep4Result(data);
            if (createBtn) createBtn.disabled = false;
        } else {
            resultDiv.innerHTML = `<div style="color: red; padding: 2rem;">Lỗi: ${data.error || 'Không thể tạo lịch trình'}</div>`;
        }
    } catch (error) {
        console.error('Step 4 error:', error);
        resultDiv.innerHTML = '<div style="color: red; padding: 2rem;">Lỗi kết nối. Vui lòng thử lại.</div>';
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
    // itinerary.itinerary is the array of daily plans from create_full_itinerary
    const dailyPlans = itinerary.daily_plans || itinerary.itinerary || [];
    const itineraryDescription = plan.itinerary_description || '';
    
    // Lấy thông tin từ JSON LICHTRINH để hiển thị ở header
    const itineraryJson = plan.itinerary_json || {};
    const lichtrinhInfo = itineraryJson.LICHTRINH && itineraryJson.LICHTRINH[0] ? itineraryJson.LICHTRINH[0] : {};
    
    // Ưu tiên lấy từ JSON LICHTRINH, fallback về các nguồn khác
    const destination = lichtrinhInfo.diemDen || workflowState.step1Data?.destination?.name || plan.destination || itinerary.destination || 'Điểm đến';
    // Ưu tiên lấy từ itinerary.total_days, sau đó từ dailyPlans.length, cuối cùng từ workflowState
    const totalDays = itinerary.total_days || dailyPlans.length || lichtrinhInfo.soNgay || workflowState.step2Data?.days || workflowState.step1Data?.days || 0;
    const soNguoi = lichtrinhInfo.soNguoi || workflowState.step1Data?.travelers || 2;
    const phongCach = lichtrinhInfo.phongCach || workflowState.step1Data?.travel_style || 'standard';
    const ngayBatDau = lichtrinhInfo.ngayBatDau || workflowState.step1Data?.start_date || '';
    const ngayKetThuc = lichtrinhInfo.ngayKetThuc || '';
    const diemXuatPhat = lichtrinhInfo.diemXuatPhat || workflowState.step1Data?.origin?.name || '';
    
    // Format phong cách để hiển thị đẹp hơn
    const phongCachLabels = {
        'eco': 'Sinh thái bền vững',
        'budget': 'Tiết kiệm',
        'standard': 'Tiêu chuẩn',
        'luxury': 'Cao cấp',
        'romantic': 'Lãng mạn',
        'adventure': 'Phiêu lưu',
        'cultural': 'Văn hóa',
        'gastronomy': 'Ẩm thực',
        'wellness': 'Sức khỏe',
        'family': 'Gia đình'
    };
    const phongCachDisplay = phongCachLabels[phongCach] || phongCach;
    
    // Tạo thông tin hiển thị cho header từ JSON LICHTRINH
    let scheduleInfo = `Lịch trình ${totalDays} ngày`;
    if (ngayBatDau && ngayKetThuc) {
        // Format ngày để hiển thị đẹp hơn (DD/MM/YYYY)
        try {
            const startDate = new Date(ngayBatDau);
            const endDate = new Date(ngayKetThuc);
            const startFormatted = `${startDate.getDate()}/${startDate.getMonth() + 1}/${startDate.getFullYear()}`;
            const endFormatted = `${endDate.getDate()}/${endDate.getMonth() + 1}/${endDate.getFullYear()}`;
            scheduleInfo += ` (${startFormatted} - ${endFormatted})`;
        } catch (e) {
            scheduleInfo += ` (${ngayBatDau} - ${ngayKetThuc})`;
        }
    }
    if (soNguoi) {
        scheduleInfo += ` • ${soNguoi} người`;
    }
    if (phongCachDisplay) {
        scheduleInfo += ` • ${phongCachDisplay}`;
    }
    if (diemXuatPhat) {
        scheduleInfo += ` • Từ ${diemXuatPhat}`;
    }
    
    // Destination header với thông tin từ JSON LICHTRINH
    let destinationHTML = `
        <div style="margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(135deg, var(--color-secondary) 0%, var(--color-secondary-dark) 100%); border-radius: 12px; color: white;">
            <h3 style="color: white; margin: 0; font-size: 1.5rem; font-weight: 600;">📍 ${destination}</h3>
            <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem; margin: 0;">${scheduleInfo}</p>
        </div>
    `;
    
    let activitiesHTML = '';
    if (activities.length > 0) {
        activitiesHTML = `
            <div style="margin-top: 2rem;">
                <h4 style="margin-bottom: 1rem; color: var(--color-primary-dark);">🎯 Hoạt động đề xuất</h4>
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    ${activities.slice(0, 5).map(activity => `
                        <div class="itinerary-activity" style="padding: 0.75rem; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                            <strong style="color: #153D68; font-size: 1rem; display: block;">${activity.name || 'N/A'}</strong>
                            ${activity.description ? `<div style="color: #6c757d; font-size: 0.9rem; margin-top: 0.25rem;">${activity.description}</div>` : ''}
                            ${activity.cost_vnd ? `<div style="color: #6c757d; font-size: 0.9rem; margin-top: 0.25rem;">Chi phí: ${formatCurrency(activity.cost_vnd)} VNĐ</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    let itineraryHTML = '';
    if (dailyPlans.length > 0) {
        itineraryHTML = `
            <div style="margin-top: 2rem;">
                <h4 style="margin-bottom: 1rem; color: var(--color-primary-dark);">📅 Lịch trình chi tiết</h4>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    ${dailyPlans.map((dayPlan, index) => {
                        const day = dayPlan.day || (index + 1);
                        // Lấy thông tin ngày từ JSON LICHTRINH nếu có (từ chiTietNgay)
                        const chiTietNgay = lichtrinhInfo.chiTietNgay || [];
                        const ngayInfo = chiTietNgay.find(n => n.ngayThu === day) || {};
                        const date = ngayInfo.ngay || dayPlan.date || '';
                        const theme = ngayInfo.chuDe || dayPlan.theme || '';
                        const thoiGianBatDau = ngayInfo.thoiGianBatDau || '';
                        const thoiGianKetThuc = ngayInfo.thoiGianKetThuc || '';
                        const meals = dayPlan.meals || {};
                        const activities_list = dayPlan.activities || [];
                        const tips = dayPlan.tips || [];
                        const dayId = `day-${index}`;
                        
                        // Count activities
                        const activityCount = ngayInfo.soHoatDong || activities_list.length;
                        const totalHours = Math.ceil(activityCount * 1.5); // Estimate
                        
                        // Tạo tiêu đề ngày với thời gian từ JSON LICHTRINH
                        let dayTitle = `📆 Ngày ${day}`;
                        if (date) {
                            try {
                                const dateObj = new Date(date);
                                const dateFormatted = `${dateObj.getDate()}/${dateObj.getMonth() + 1}/${dateObj.getFullYear()}`;
                                dayTitle += ` (${dateFormatted})`;
                            } catch (e) {
                                dayTitle += ` (${date})`;
                            }
                        }
                        if (thoiGianBatDau && thoiGianKetThuc) {
                            dayTitle += ` • ${thoiGianBatDau} - ${thoiGianKetThuc}`;
                        } else if (thoiGianBatDau) {
                            dayTitle += ` • Bắt đầu: ${thoiGianBatDau}`;
                        }
                        if (theme) {
                            dayTitle += `: ${theme}`;
                        }
                        
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
                            
                            mealsHTML = '<div style="margin-top: 0.75rem;"><strong style="color: #153D68;">🍽️ Bữa ăn:</strong><div style="margin-top: 0.5rem; padding-left: 1rem;">';
                            Object.keys(mealLabels).forEach(mealType => {
                                if (meals[mealType]) {
                                    const meal = meals[mealType];
                                    const mealName = typeof meal === 'string' ? meal : (meal.name || 'N/A');
                                    mealsHTML += `<div style="margin-bottom: 0.25rem; color: #6c757d;">${mealLabels[mealType]}: ${mealName}</div>`;
                                }
                            });
                            mealsHTML += '</div></div>';
                        }
                        
                        let activitiesHTML_day = '';
                        
                        // Lấy timeline từ dayPlan nếu có (có thời gian cụ thể hơn)
                        const timeline = dayPlan.timeline || [];
                        const activitiesToShow = timeline.length > 0 ? timeline : activities_list;
                        
                        if (activitiesToShow.length > 0) {
                            activitiesHTML_day = '<div style="margin-top: 0.75rem;"><strong style="color: #153D68;">🎯 Hoạt động:</strong><div style="margin-top: 0.5rem;">';
                            
                            activitiesToShow.forEach((actItem, idx) => {
                                if (typeof actItem === 'string') {
                                    activitiesHTML_day += `<div class="itinerary-activity" style="margin-bottom: 0.75rem; padding: 0.75rem; background: white; border-radius: 8px; border-left: 3px solid #00838F;">${actItem}</div>`;
                                } else if (typeof actItem === 'object') {
                                    const time = actItem.time || actItem.time_slot || '';
                                    const endTime = actItem.end_time || '';
                                    const actDesc = actItem.description || '';
                                    const activity = actItem.activity || actItem.activity_details || {};
                                    const actName = typeof activity === 'string' ? activity : (activity.name || actItem.label || 'Hoạt động');
                                    const actType = actItem.type || '';
                                    
                                    // Xác định màu và icon dựa trên loại hoạt động
                                    let borderColor = '#00838F';
                                    let icon = '📍';
                                    if (actType === 'meal') {
                                        borderColor = '#DAA520';
                                        icon = '🍽️';
                                    } else if (actType === 'free_time') {
                                        borderColor = '#9E9E9E';
                                        icon = '⏰';
                                    } else if (actType === 'rest') {
                                        borderColor = '#757575';
                                        icon = '😴';
                                    } else if (actType === 'transport') {
                                        borderColor = '#1976D2';
                                        icon = '🚗';
                                    }
                                    
                                    activitiesHTML_day += `<div class="itinerary-activity" style="margin-bottom: 0.75rem; padding: 0.75rem; background: white; border-radius: 8px; border-left: 3px solid ${borderColor};">`;
                                    
                                    // Hiển thị thời gian
                                    if (time) {
                                        let timeDisplay = time;
                                        if (endTime) {
                                            timeDisplay = `${time} - ${endTime}`;
                                        }
                                        activitiesHTML_day += `<div style="font-weight: 600; color: ${borderColor}; margin-bottom: 0.25rem; font-size: 0.9rem;">${icon} ${timeDisplay}</div>`;
                                    }
                                    
                                    activitiesHTML_day += `<div style="font-weight: 600; color: #153D68; margin-bottom: 0.25rem;">${actName}</div>`;
                                    
                                    if (actDesc) {
                                        activitiesHTML_day += `<div style="color: #6c757d; font-size: 0.9rem; margin-top: 0.25rem; line-height: 1.5;">${actDesc}</div>`;
                                    }
                                    
                                    // Hiển thị thông tin bổ sung cho free time
                                    if (actType === 'free_time' && actItem.duration_minutes) {
                                        const hours = Math.floor(actItem.duration_minutes / 60);
                                        const minutes = actItem.duration_minutes % 60;
                                        let durationText = '';
                                        if (hours > 0) {
                                            durationText = `${hours} giờ`;
                                            if (minutes > 0) {
                                                durationText += ` ${minutes} phút`;
                                            }
                                        } else {
                                            durationText = `${minutes} phút`;
                                        }
                                        activitiesHTML_day += `<div style="color: #9E9E9E; font-size: 0.85rem; margin-top: 0.25rem; font-style: italic;">⏱️ Thời lượng: ${durationText}</div>`;
                                    }
                                    
                                    activitiesHTML_day += `</div>`;
                                }
                            });
                            activitiesHTML_day += '</div></div>';
                        }
                        
                        let tipsHTML = '';
                        if (tips.length > 0) {
                            tipsHTML = '<div style="margin-top: 0.75rem;"><strong style="color: #153D68;">💡 Mẹo:</strong><ul style="margin-top: 0.5rem; padding-left: 1.5rem; color: #6c757d;">';
                            tips.slice(0, 3).forEach(tip => {
                                tipsHTML += `<li style="margin-bottom: 0.25rem;">${tip}</li>`;
                            });
                            tipsHTML += '</ul></div>';
                        }
                        
                        return `
                            <div class="day-card" style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 1rem;">
                                <div class="day-card-header" onclick="toggleDay('${dayId}')" style="padding: 1rem 1.5rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: white; border-bottom: 1px solid #e0e0e0;">
                                    <div>
                                        <h4 style="color: #153D68; margin: 0; font-size: 1.1rem; font-weight: 600;">
                                            ${dayTitle}
                                        </h4>
                                        <div style="color: #6c757d; font-size: 0.85rem; margin-top: 0.25rem;">
                                            ${activityCount} hoạt động • ${totalHours} tiếng
                                        </div>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <button style="background: #DAA520; color: white; border: none; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.85rem; cursor: pointer; display: flex; align-items: center; gap: 0.25rem;">
                                            <i class="fa-solid fa-note-sticky"></i> Ghi chú
                                        </button>
                                        <span class="day-toggle-icon" id="icon-${dayId}" style="font-size: 1.2rem; color: #00838F; transition: transform 0.3s; cursor: pointer;">
                                            <i class="fa-solid fa-chevron-down"></i>
                                        </span>
                                    </div>
                                </div>
                                <div class="day-card-content" id="${dayId}" style="display: none; padding: 1.5rem; background: #f8f9fa;">
                                    ${mealsHTML}
                                    ${activitiesHTML_day}
                                    ${tipsHTML}
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    // Hiển thị itinerary description nếu có (LLM-generated)
    let descriptionHTML = '';
    if (itineraryDescription && itineraryDescription.trim()) {
        descriptionHTML = `
            <div style="margin-top: 2rem; padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border-left: 4px solid var(--color-secondary);">
                <h4 style="margin-bottom: 1rem; color: var(--color-primary-dark);">📝 Mô tả lịch trình</h4>
                <div style="color: #495057; line-height: 1.8; white-space: pre-wrap; font-size: 0.95rem;">${itineraryDescription}</div>
            </div>
        `;
    }
    
    resultDiv.innerHTML = `
        ${destinationHTML}
        <div class="budget-breakdown">
            <h4>💰 Tổng kết chi phí</h4>
            <div class="budget-item">
                <span>Di chuyển</span>
                <span>${formatCurrency(costs.transport || 0)} VNĐ</span>
            </div>
            <div class="budget-item">
                <span>Lưu trú</span>
                <span>${formatCurrency(costs.accommodation || 0)} VNĐ</span>
            </div>
            <div class="budget-item">
                <span>Hoạt động</span>
                <span>${formatCurrency(costs.activities || 0)} VNĐ</span>
            </div>
            <div class="budget-item">
                <span>Ăn uống</span>
                <span>${formatCurrency(costs.dining || 0)} VNĐ</span>
            </div>
            <div class="budget-item">
                <span>Tổng cộng</span>
                <span>${formatCurrency(costs.total || 0)} VNĐ</span>
            </div>
        </div>
        ${descriptionHTML}
        ${activitiesHTML}
        ${itineraryHTML}
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
    // This will be called when user clicks "Tạo lịch trình"
    // Save itinerary to database
    
    if (!workflowState.step4Data) {
        showErrorModal('Vui lòng tạo lịch trình trước khi lưu', 'error');
        return;
    }
    
    const saveBtn = document.getElementById('step4-create');
    if (saveBtn) {
        saveBtn.disabled = true;
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="loading-spinner"></span> Đang lưu...';
        
        try {
            // Prepare data to save
            const plan = workflowState.step4Data.plan || {};
            const costs = workflowState.step4Data.costs || {};
            
            const payload = {
                origin: workflowState.step1Data.origin.name,
                destination: workflowState.step1Data.destination.name,
                start_date: workflowState.step2Data.start_date,
                days: workflowState.step2Data.days,
                travelers: workflowState.step2Data.travelers,
                travel_style: workflowState.step2Data.travel_style,
                plan: plan,
                costs: costs
            };
            
            const response = await fetch('/api/v1/travel-plans/step4/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'success') {
                showErrorModal('Lịch trình đã được lưu thành công!', 'success');
                // Optionally redirect to itinerary detail page
                setTimeout(() => {
                    window.location.href = `/accounts/itineraries/`;
                }, 2000);
            } else {
                showErrorModal('Lỗi: ' + (data.error || 'Không thể lưu lịch trình'), 'error');
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = originalText;
                }
            }
        } catch (error) {
            console.error('Error saving itinerary:', error);
            showErrorModal('Lỗi kết nối. Vui lòng thử lại.', 'error');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
            }
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
window.selectTransport = selectTransport;
window.continueToStep3 = continueToStep3;

