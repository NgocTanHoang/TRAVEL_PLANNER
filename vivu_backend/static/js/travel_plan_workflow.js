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

// Step 3: Budget & Hotels
async function loadStep3() {
    const resultDiv = document.getElementById('step3-result');
    const continueBtn = document.getElementById('step3-continue');
    
    if (!resultDiv) return;
    
    resultDiv.innerHTML = '<div style="text-align: center; padding: 3rem;"><p>Đang tải thông tin...</p></div>';
    
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
                <div class="hotels-grid">
                    ${hotels.map((hotel, index) => `
                        <div class="hotel-card" onclick="selectHotel(${index})" data-hotel-index="${index}">
                            <div class="hotel-name">${hotel.name || 'N/A'}</div>
                            ${hotel.stars ? `<div class="hotel-rating">${'⭐'.repeat(hotel.stars)} ${hotel.rating || ''}/5</div>` : ''}
                            ${hotel.price_per_night ? `<div class="hotel-price">${formatCurrency(hotel.price_per_night)} VNĐ/đêm</div>` : ''}
                            ${hotel.source ? `<div style="font-size: 0.85rem; color: var(--color-gray-600); margin-top: 0.5rem;">Nguồn: ${hotel.source}</div>` : ''}
                        </div>
                    `).join('')}
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
    const dailyPlans = itinerary.daily_plans || itinerary.itinerary || [];
    
    // Get destination from workflow state
    const destination = workflowState.step1Data?.destination?.name || plan.destination || 'Điểm đến';
    
    // Destination header
    let destinationHTML = `
        <div style="margin-bottom: 2rem; padding: 1.5rem; background: linear-gradient(135deg, var(--color-secondary) 0%, var(--color-secondary-dark) 100%); border-radius: 12px; color: white;">
            <h3 style="color: white; margin: 0; font-size: 1.5rem; font-weight: 600;">📍 ${destination}</h3>
            <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem; margin: 0;">Lịch trình ${dailyPlans.length} ngày</p>
        </div>
    `;
    
    let activitiesHTML = '';
    if (activities.length > 0) {
        activitiesHTML = `
            <div style="margin-top: 2rem;">
                <h4 style="margin-bottom: 1rem; color: var(--color-primary-dark);">🎯 Hoạt động đề xuất</h4>
                <div>
                    ${activities.slice(0, 5).map(activity => `
                        <div class="itinerary-activity" style="color: #153D68;">
                            <strong style="color: #153D68; font-size: 1rem;">${activity.name || 'N/A'}</strong>
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
                        if (activities_list.length > 0) {
                            activitiesHTML_day = '<div style="margin-top: 0.75rem;"><strong style="color: #153D68;">🎯 Hoạt động:</strong><div style="margin-top: 0.5rem;">';
                            activities_list.forEach(actItem => {
                                if (typeof actItem === 'string') {
                                    activitiesHTML_day += `<div class="itinerary-activity" style="margin-bottom: 0.5rem; color: #153D68;">${actItem}</div>`;
                                } else if (typeof actItem === 'object') {
                                    const time = actItem.time || actItem.time_slot || '';
                                    const actDesc = actItem.description || '';
                                    const activity = actItem.activity || {};
                                    const actName = typeof activity === 'string' ? activity : (activity.name || 'Hoạt động');
                                    
                                    activitiesHTML_day += `<div class="itinerary-activity" style="margin-bottom: 0.5rem; color: #153D68;">`;
                                    if (time) {
                                        activitiesHTML_day += `<div style="font-weight: 600; color: #00838F; margin-bottom: 0.25rem;">${time}</div>`;
                                    }
                                    activitiesHTML_day += `<div style="font-weight: 600; color: #153D68;">${actName}</div>`;
                                    if (actDesc) {
                                        activitiesHTML_day += `<div style="color: #6c757d; font-size: 0.9rem; margin-top: 0.25rem;">${actDesc}</div>`;
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
                            <div class="day-card" style="background: #f8f9fa; border-radius: 12px; overflow: hidden; border: 1px solid #e0e0e0;">
                                <div class="day-card-header" onclick="toggleDay('${dayId}')" style="padding: 1rem 1.5rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: white; border-bottom: 1px solid #e0e0e0;">
                                    <div>
                                        <h4 style="color: #153D68; margin: 0; font-size: 1.1rem; font-weight: 600;">
                                            📆 Ngày ${day}${date ? ` (${date})` : ''}${theme ? `: ${theme}` : ''}
                                        </h4>
                                        <div style="color: #6c757d; font-size: 0.85rem; margin-top: 0.25rem;">
                                            ${activityCount} hoạt động • ${totalHours} tiếng
                                        </div>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <button style="background: #DAA520; color: white; border: none; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.85rem; cursor: pointer;">Ghi chú</button>
                                        <span class="day-toggle-icon" id="icon-${dayId}" style="font-size: 1.2rem; color: #00838F; transition: transform 0.3s;">▼</span>
                                    </div>
                                </div>
                                <div class="day-card-content" id="${dayId}" style="display: none; padding: 1.5rem;">
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
        icon.textContent = '▲';
        icon.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
        icon.style.transform = 'rotate(0deg)';
    }
}

function createFinalPlan() {
    // This will be called when user clicks "Tạo lịch trình"
    // For now, just show success message
    showErrorModal('Lịch trình đã được tạo thành công! (Trong tương lai sẽ lưu vào database)', 'success');
    
    // In the future, you might want to:
    // 1. Save to database
    // 2. Redirect to itinerary detail page
    // 3. Show success message with link
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
    return new Intl.NumberFormat('vi-VN').format(amount);
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

// Export functions for use in HTML
window.goToStep = goToStep;
window.selectHotel = selectHotel;
window.createFinalPlan = createFinalPlan;
window.toggleDay = toggleDay;

