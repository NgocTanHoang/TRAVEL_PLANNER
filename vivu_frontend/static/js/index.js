        // Navbar scroll effect
        const navbar = document.getElementById('navbar');
        if (navbar) {
            window.addEventListener('scroll', () => {
                if (window.pageYOffset > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            });
        }

        // Mobile menu toggle
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        if (mobileMenuToggle && navMenu) {
            mobileMenuToggle.addEventListener('click', () => {
                const isOpen = navMenu.style.display === 'flex';
                navMenu.style.display = isOpen ? 'none' : 'flex';
                if (!isOpen) {
                    navMenu.style.flexDirection = 'column';
                    navMenu.style.position = 'absolute';
                    navMenu.style.top = '100%';
                    navMenu.style.left = '0';
                    navMenu.style.right = '0';
                    navMenu.style.background = 'var(--color-primary-dark)';
                    navMenu.style.padding = '1rem';
                }
            });
        }

        // User location for distance calculation
        let userLocation = null;

        // Format JSON string to Vietnamese text
        function formatJsonToVietnamese(jsonStr) {
            if (!jsonStr) return '';
            
            try {
                // Try to parse as JSON
                const parsed = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr;
                
                if (typeof parsed === 'object' && parsed !== null) {
                    const items = [];
                    for (const [key, value] of Object.entries(parsed)) {
                        const keyVi = translateToVietnamese(key);
                        if (typeof value === 'boolean') {
                            if (value) {
                                items.push(keyVi);
                            }
                        } else if (typeof value === 'number') {
                            items.push(`${keyVi}: ${value}`);
                        } else if (typeof value === 'string') {
                            items.push(`${keyVi}: ${value}`);
                        } else {
                            items.push(keyVi);
                        }
                    }
                    return items.join(', ');
                }
            } catch (e) {
                // Not JSON, return as is but clean it
                return cleanVietnameseText(jsonStr);
            }
            
            return cleanVietnameseText(jsonStr);
        }

        // Translate English to Vietnamese (simple mapping)
        function translateToVietnamese(text) {
            const translations = {
                'architectural_origin': 'Kiến trúc',
                'French-colonial': 'Pháp thuộc địa',
                'rooms': 'Số phòng',
                'image_url': 'Ảnh',
                'spa': 'Spa',
                'pool': 'Hồ bơi',
                'lounge': 'Phòng chờ',
                'gym': 'Phòng gym',
                'restaurant': 'Nhà hàng',
                'bar': 'Quầy bar',
                'wifi': 'Wi-Fi',
                'parking': 'Bãi đỗ xe',
                'concierge': 'Lễ tân',
                'room_service': 'Dịch vụ phòng',
                'laundry': 'Giặt ủi',
                'business_center': 'Trung tâm kinh doanh',
                'meeting_rooms': 'Phòng họp',
                'airport_shuttle': 'Xe đưa đón sân bay',
                'pet_friendly': 'Cho phép thú cưng',
                'smoking': 'Hút thuốc',
                'non_smoking': 'Không hút thuốc',
                'breakfast': 'Bữa sáng',
                'true': 'Có',
                'false': 'Không'
            };
            
            const lowerText = text.toLowerCase().trim();
            return translations[lowerText] || text;
        }

        // Clean and normalize Vietnamese text
        function cleanVietnameseText(text) {
            if (!text) return '';
            
            // Remove JSON-like patterns
            text = text.replace(/\{[^}]*\}/g, '');
            text = text.replace(/\[[^\]]*\]/g, '');
            
            // Remove English text patterns (keep only Vietnamese)
            // This is a simple heuristic - remove sentences that are mostly English
            const sentences = text.split(/[.!?]\s+/);
            const vietnameseSentences = sentences.filter(sentence => {
                // Count Vietnamese characters (with diacritics)
                const vietnameseChars = (sentence.match(/[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]/g) || []).length;
                const totalChars = sentence.replace(/\s+/g, '').length;
                
                // If more than 30% Vietnamese characters, keep it
                if (totalChars === 0) return false;
                return (vietnameseChars / totalChars) > 0.3;
            });
            
            // Join and clean
            let cleaned = vietnameseSentences.join('. ');
            
            // Remove common English phrases
            cleaned = cleaned.replace(/\b(English below|Dear [A-Za-z]+,|Thank you|We hope|Rest assured|Once again|This is|Park Hyatt|Saigon|Ho Chi Minh City)\b[^.]*\./gi, '');
            
            // Remove email-like patterns
            cleaned = cleaned.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '');
            
            // Normalize whitespace
            cleaned = cleaned.replace(/\s+/g, ' ').trim();
            
            // Ensure proper sentence endings
            if (cleaned && !cleaned.match(/[.!?]$/)) {
                cleaned += '.';
            }
            
            return cleaned;
        }

        // Calculate distance between two coordinates (Haversine formula)
        function calculateDistance(lat1, lon1, lat2, lon2) {
            // Validate inputs - check for null/undefined, not for falsy values (0 is valid)
            if (lat1 === null || lat1 === undefined || lon1 === null || lon1 === undefined ||
                lat2 === null || lat2 === undefined || lon2 === null || lon2 === undefined ||
                isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
                console.warn('Invalid coordinates for distance calculation:', {lat1, lon1, lat2, lon2});
                return Infinity;
            }
            
            // Validate coordinate ranges
            if (lat1 < -90 || lat1 > 90 || lat2 < -90 || lat2 > 90 ||
                lon1 < -180 || lon1 > 180 || lon2 < -180 || lon2 > 180) {
                console.warn('Coordinates out of valid range:', {lat1, lon1, lat2, lon2});
                return Infinity;
            }
            
            const R = 6371; // Radius of Earth in km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = 
                Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            return R * c; // Distance in km
        }

        // Format giá tiền với đơn vị VND (hiển thị số đầy đủ với dấu phẩy ngăn cách)
        function formatPrice(price) {
            if (!price || price === 0) {
                return 'Miễn phí';
            }
            // Format số với dấu phẩy ngăn cách hàng nghìn và đơn vị VND
            return `${Math.round(price).toLocaleString('vi-VN')} VND`;
        }

        // Format khoảng cách (km hoặc m) - Đảm bảo function có thể truy cập được
        function formatDistance(distance) {
            if (distance === null || distance === undefined || distance === Infinity || isNaN(distance)) {
                return 'Không xác định';
            }
            
            // Nếu khoảng cách < 1km, hiển thị bằng mét
            if (distance < 1) {
                const meters = Math.round(distance * 1000);
                return `${meters} m`;
            }
            
            // Nếu khoảng cách >= 1km, hiển thị bằng km với 1 chữ số thập phân
            return `${distance.toFixed(1)} km`;
        }
        
        // Export formatDistance to window để đảm bảo có thể truy cập được
        if (typeof window !== 'undefined') {
            window.formatDistance = formatDistance;
        }

        // Load Popular Places (horizontal scroll)
        function loadPopularPlaces() {
            const container = document.getElementById('popular-places-horizontal');
            if (!container) return;

            fetch('/api/v1/places/?ordering=-danhGiaTrungBinh,-soLuotDanhGia&limit=10')
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        container.innerHTML = '';
                        data.results.forEach(place => {
                            const bar = createPlaceBar(place, null, true); // true = isPopular
                            container.appendChild(bar);
                        });
                        startAutoScroll('popular-scroll');
                        setupDragScroll('popular-scroll');
                    } else {
                        container.innerHTML = '<div class="loading-placeholder">Không tìm thấy địa điểm phổ biến</div>';
                    }
                })
                .catch(error => {
                    console.error('Error loading popular places:', error);
                    container.innerHTML = '<div class="loading-placeholder">Không thể tải địa điểm phổ biến</div>';
                });
        }

        // Load Recommended Places
        function loadRecommendedPlaces() {
            const container = document.getElementById('recommended-places-horizontal');
            if (!container) return;

            fetch('/api/v1/places/?ordering=-soLuotDanhGia,-danhGiaTrungBinh&limit=10')
                .then(response => response.json())
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        container.innerHTML = '';
                        data.results.forEach(place => {
                            const bar = createPlaceBar(place, null);
                            container.appendChild(bar);
                        });
                        startAutoScroll('recommended-scroll');
                    } else {
                        container.innerHTML = '<div class="loading-placeholder">Không tìm thấy địa điểm đề xuất</div>';
                    }
                })
                .catch(error => {
                    console.error('Error loading recommended places:', error);
                    container.innerHTML = '<div class="loading-placeholder">Không thể tải địa điểm đề xuất</div>';
                });
        }

        // Load Nearby Places with distance sorting
        function loadNearbyPlaces() {
            const container = document.getElementById('nearby-places-list');
            if (!container) return;

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        userLocation = {
                            lat: position.coords.latitude,
                            lon: position.coords.longitude
                        };
                        
                        fetch('/api/v1/places/?limit=20')
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(`HTTP error! status: ${response.status}`);
                                }
                                return response.json();
                            })
                            .then(data => {
                                console.log('Nearby places API response:', data); // Debug log
                                if (data.results && data.results.length > 0) {
                                    const placesWithDistance = data.results.map(place => {
                                        // viDo = latitude (vĩ độ), kinhDo = longitude (kinh độ)
                                        const placeLat = parseFloat(place.viDo || place.latitude || 21.0285);
                                        const placeLon = parseFloat(place.kinhDo || place.longitude || 105.8542);
                                        
                                        // Validate coordinates
                                        let distance = Infinity;
                                        if (!isNaN(placeLat) && !isNaN(placeLon) && 
                                            placeLat >= -90 && placeLat <= 90 && 
                                            placeLon >= -180 && placeLon <= 180 &&
                                            !isNaN(userLocation.lat) && !isNaN(userLocation.lon)) {
                                            distance = calculateDistance(
                                                userLocation.lat, 
                                                userLocation.lon,
                                                placeLat,
                                                placeLon
                                            );
                                        }
                                        
                                        return { ...place, distance, placeLat, placeLon };
                                    });
                                    
                                    placesWithDistance.sort((a, b) => {
                                        const distDiff = Math.abs(a.distance - b.distance);
                                        if (distDiff < 0.1) {
                                            return (b.danhGiaTrungBinh || b.rating || 0) - (a.danhGiaTrungBinh || a.rating || 0);
                                        }
                                        return a.distance - b.distance;
                                    });
                                    
                                    container.innerHTML = '';
                                    placesWithDistance.slice(0, 10).forEach(place => {
                                        console.log('Creating place bar for:', place.tenDiaDiem, place); // Debug log
                                        const bar = createPlaceBar(place, place.distance, false); // false = not popular
                                        container.appendChild(bar);
                                    });
                                } else {
                                    console.warn('No results from nearby places API');
                                    container.innerHTML = '<div class="loading-placeholder">Không tìm thấy địa điểm gần đây</div>';
                                }
                            })
                            .catch(error => {
                                console.error('Error loading nearby places:', error);
                                container.innerHTML = '<div class="loading-placeholder">Không thể tải địa điểm gần đây: ' + error.message + '</div>';
                            });
                    },
                    error => {
                        console.warn('Geolocation error:', error);
                        // Fallback: load places without geolocation
                        fetch('/api/v1/places/?limit=10')
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(`HTTP error! status: ${response.status}`);
                                }
                                return response.json();
                            })
                            .then(data => {
                                if (data.results && data.results.length > 0) {
                                    container.innerHTML = '';
                                    data.results.forEach(place => {
                                        const bar = createPlaceBar(place, null, false); // false = not popular
                                        container.appendChild(bar);
                                    });
                                } else {
                                    container.innerHTML = '<div class="loading-placeholder">Không tìm thấy địa điểm gần đây</div>';
                                }
                            })
                            .catch(error => {
                                console.error('Error loading nearby places (fallback):', error);
                                container.innerHTML = '<div class="loading-placeholder">Không thể tải địa điểm gần đây</div>';
                            });
                    }
                );
            } else {
                // Browser không hỗ trợ geolocation
                fetch('/api/v1/places/?limit=10')
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            container.innerHTML = '';
                            data.results.forEach(place => {
                                const bar = createPlaceBar(place, null, false);
                                container.appendChild(bar);
                            });
                        } else {
                            container.innerHTML = '<div class="loading-placeholder">Không tìm thấy địa điểm gần đây</div>';
                        }
                    })
                    .catch(error => {
                        console.error('Error loading nearby places:', error);
                        container.innerHTML = '<div class="loading-placeholder">Không thể tải địa điểm gần đây</div>';
                    });
            }
        }

        // Create place bar (horizontal) element
        function createPlaceBar(place, distance, isPopular = false) {
            const bar = document.createElement('div');
            bar.className = 'place-bar';

            // Lấy ảnh chính từ hinhAnhChinh (API list) hoặc hinhAnhs (API detail) hoặc anhDaiDien
            let imageUrl = place.hinhAnhChinh || '';
            if (!imageUrl && place.hinhAnhs && place.hinhAnhs.length > 0) {
                // Tìm ảnh chính (laChinh = true) hoặc ảnh đầu tiên
                const mainImage = place.hinhAnhs.find(img => img.laChinh) || place.hinhAnhs[0];
                imageUrl = mainImage.urlHinhAnh || '';
            }
            if (!imageUrl) {
                imageUrl = place.anhDaiDien || place.image || '';
            }
            const rating = place.danhGiaTrungBinh || place.rating || 0;
            const ratingCount = place.soLuotDanhGia || place.review_count || 0;
            const location = place.tenTinhThanh || (place.maTinhThanh && place.maTinhThanh.tenTinhThanh) || place.city || 'Chưa xác định';
            const address = place.diaChi || place.address || '';
            const price = place.giaVe || place.price || 0;
            // Format giờ mở cửa: nếu có cả gioMoCua và gioDongCua thì ghép lại
            let openHours = '08:00 - 22:00'; // Default
            if (place.gioMoCua && place.gioDongCua) {
                openHours = `${place.gioMoCua} - ${place.gioDongCua}`;
            } else if (place.gioMoCua) {
                openHours = `${place.gioMoCua} - 22:00`;
            } else if (place.gioDongCua) {
                openHours = `08:00 - ${place.gioDongCua}`;
            } else if (place.open_hours) {
                openHours = place.open_hours;
            }
            
            const priceText = formatPrice(price);
            
            // Format distance trước khi đưa vào template string
            let distanceText = '';
            if (distance !== null && distance !== undefined && distance !== Infinity) {
                try {
                    distanceText = formatDistance(distance);
                } catch (e) {
                    console.error('Error formatting distance:', e);
                    distanceText = distance < 1 ? `${Math.round(distance * 1000)} m` : `${distance.toFixed(1)} km`;
                }
            }
            
            const fullStars = Math.floor(rating);
            const hasHalfStar = (rating % 1) >= 0.5;
            const stars = '★'.repeat(fullStars) + (hasHalfStar ? '½' : '') + '☆'.repeat(5 - fullStars - (hasHalfStar ? 1 : 0));

            // Nếu là phần "Phổ biến", không có nút chi tiết
            const infoButton = isPopular ? '' : `
                <button class="place-bar-info-btn" onclick="event.stopPropagation(); showNearbyPlaceDetail(${place.maDiaDiem || place.id})" title="Xem thông tin chi tiết">
                    ℹ️ Chi tiết
                </button>`;

            bar.innerHTML = `
                <div class="place-bar-image" style="${imageUrl ? `background-image: url('${imageUrl}'); background-size: cover; background-position: center;` : ''}">
                    ${!imageUrl ? '<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 2rem;">📍</div>' : ''}
                </div>
                <div class="place-bar-content">
                    <!-- Hàng 1: Tên địa điểm -->
                    <h3 class="place-bar-title">${place.tenDiaDiem || place.name || 'Địa điểm'}</h3>
                    
                    <!-- Hàng 2: Giá, giờ mở cửa, rating -->
                    <div class="place-bar-info-row">
                        <div class="place-bar-info-item">
                            <strong>💰</strong> ${priceText}
                        </div>
                        <div class="place-bar-info-item">
                            <strong>🕐</strong> ${openHours}
                        </div>
                        <div class="place-bar-rating">
                            <span class="rating-stars">${stars}</span>
                            <span class="rating-score">${rating > 0 ? rating.toFixed(1) : 'N/A'}</span>
                        </div>
                    </div>
                    
                    <!-- Hàng 3: Khoảng cách và nút thêm (hoặc nút chi tiết nếu không phải popular) -->
                    <div class="place-bar-bottom">
                        ${distanceText ? `<div class="place-bar-distance">📍 ${distanceText}</div>` : '<div></div>'}
                        <div class="place-bar-actions">
                            ${infoButton}
                            <button class="place-bar-add-btn" onclick="event.stopPropagation(); addToItinerary('${place.maDiaDiem || place.id}')">
                                ➕ Thêm
                            </button>
                        </div>
                    </div>
                </div>
            `;

            // Nếu là phần "Phổ biến", không có onclick redirect, chỉ để drag
            if (!isPopular) {
                // Cho phần "Địa điểm gần đây": click vào địa điểm sẽ hiển thị thông tin ở cột bên phải
                bar.onclick = (e) => {
                    // Chỉ trigger nếu không click vào button
                    if (!e.target.closest('button')) {
                        showNearbyPlaceDetail(place.maDiaDiem || place.id);
                    }
                };
                // Lưu placeId vào data attribute để dễ tìm
                bar.setAttribute('data-place-id', place.maDiaDiem || place.id);
            }
            // Popular places không có onclick, để có thể drag tự do

            return bar;
        }

        // Auto-scroll function - Chuyển địa điểm mỗi 30-45 giây
        function startAutoScroll(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const scrollInterval = container.querySelector('.place-bar');
            if (!scrollInterval) return; // Chưa có địa điểm
            
            const placeBarWidth = scrollInterval.offsetWidth;
            const gap = 24; // 1.5rem = 24px
            const itemWidth = placeBarWidth + gap;
            
            let currentIndex = 0;
            const minDelay = 30000; // 30 giây
            const maxDelay = 45000; // 45 giây
            
            function scrollToNext() {
                const maxScroll = container.scrollWidth - container.clientWidth;
                if (maxScroll <= 0) return; // Không cần scroll
                
                currentIndex++;
                const targetScroll = currentIndex * itemWidth;
                
                // Nếu đã hết, quay lại đầu
                if (targetScroll > maxScroll) {
                    currentIndex = 0;
                    container.scrollTo({
                        left: 0,
                        behavior: 'smooth'
                    });
                } else {
                    container.scrollTo({
                        left: targetScroll,
                        behavior: 'smooth'
                    });
                }
                
                // Random delay giữa 30-45 giây
                const nextDelay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;
                setTimeout(scrollToNext, nextDelay);
            }
            
            // Bắt đầu sau 30-45 giây đầu tiên
            const initialDelay = Math.floor(Math.random() * (maxDelay - minDelay + 1)) + minDelay;
            setTimeout(scrollToNext, initialDelay);
        }

        // Drag to scroll functionality cho popular places - Mượt mà hơn
        function setupDragScroll(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            let isDown = false;
            let startX;
            let scrollLeft;

            container.addEventListener('mousedown', (e) => {
                isDown = true;
                container.style.cursor = 'grabbing';
                startX = e.pageX - container.offsetLeft;
                scrollLeft = container.scrollLeft;
                e.preventDefault();
            });

            container.addEventListener('mouseleave', () => {
                isDown = false;
                container.style.cursor = 'grab';
            });

            container.addEventListener('mouseup', () => {
                isDown = false;
                container.style.cursor = 'grab';
            });

            container.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                e.preventDefault();
                const x = e.pageX - container.offsetLeft;
                const walk = (x - startX) * 2.5; // Tăng tốc độ scroll để mượt mà hơn
                container.scrollLeft = scrollLeft - walk;
            });

            // Smooth scrolling khi wheel
            container.addEventListener('wheel', (e) => {
                if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                    e.preventDefault();

            // Remove selected class from all place bars
            document.querySelectorAll('.place-bar').forEach(bar => {
                bar.classList.remove('selected');
            });

            // Add selected class to clicked place bar
            const placeBars = document.querySelectorAll('.place-bar');
            placeBars.forEach(bar => {
                const barPlaceId = bar.getAttribute('data-place-id') || 
                                   bar.querySelector('.place-bar-add-btn')?.getAttribute('onclick')?.match(/'(\d+)'/)?.[1] || 
                                   bar.querySelector('.place-bar-info-btn')?.getAttribute('onclick')?.match(/showNearbyPlaceDetail\((\d+)\)/)?.[1];
                if (barPlaceId && barPlaceId == placeId.toString()) {
                    bar.classList.add('selected');
                }
            });

            // Scroll selected place into view (trong danh sách bên trái)
            const selectedBar = Array.from(placeBars).find(bar => bar.classList.contains('selected'));
            if (selectedBar) {
                selectedBar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }

            // Scroll đến phần thông tin chi tiết (cột bên phải) thay vì lên trên cùng
            // Scroll đến section nearby để hiển thị phần detail
            const nearbySection = document.getElementById('nearby-section');
            if (nearbySection) {
                setTimeout(() => {
                    // Scroll đến section, sau đó scroll đến detail panel
                    nearbySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    // Sau khi scroll đến section, scroll thêm một chút để detail panel vào view
                    setTimeout(() => {
                        detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
                    }, 300);
                }, 50);
            } else {
                // Fallback: scroll trực tiếp đến detail panel
                setTimeout(() => {
                    detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
                }, 100);
            }

            // Show loading
            detailPanel.className = 'nearby-place-detail';
            detailPanel.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--color-text-light);">
                    <p>Đang tải thông tin...</p>
                    <p style="font-size: 0.9rem; opacity: 0.7; margin-top: 0.5rem;">Đang tìm kiếm thông tin trên mạng...</p>
                </div>
            `;

            // Fetch enriched place data
            fetch(`/api/v1/places/${placeId}/enriched/?search_web=true`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Get image
                    let imageUrl = '';
                    if (data.hinhAnhs && data.hinhAnhs.length > 0) {
                        const mainImage = data.hinhAnhs.find(img => img.laChinh) || data.hinhAnhs[0];
                        imageUrl = mainImage.urlHinhAnh || '';
                    }
                    imageUrl = imageUrl || data.hinhAnhChinh || '';

                    const rating = data.danhGiaTrungBinh || 0;
                    const ratingCount = data.soLuotDanhGia || 0;
                    const price = data.giaVe || 0;
                    const priceText = formatPrice(price);
                    const city = data.tenTinhThanh || (data.maTinhThanh && data.maTinhThanh.tenTinhThanh) || 'Chưa xác định';

                    // Build HTML content
                    let html = '';

                    if (imageUrl) {
                        html += `<img src="${imageUrl}" alt="${data.tenDiaDiem}" class="nearby-place-detail-image">`;
                    }

                    html += `
                        <h3>${data.tenDiaDiem || 'Thông tin địa điểm'}</h3>
                        
                        <div class="nearby-place-detail-section">
                            <h4>📋 Thông tin cơ bản</h4>
                            <div class="nearby-place-detail-info">
                                ${data.diaChi && data.diaChi !== 'Chưa cập nhật' ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>📍 Địa chỉ:</strong> ${data.diaChi}
                                </div>
                                ` : ''}
                                ${city && city !== 'Chưa xác định' && city !== 'N/A' ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>🏙️ Tỉnh/Thành:</strong> ${city}
                                </div>
                                ` : ''}
                                ${priceText ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>💰 Giá vé:</strong> ${priceText}
                                </div>
                                ` : ''}
                                ${data.gioMoCua && data.gioMoCua !== 'Chưa cập nhật' ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>🕐 Giờ mở cửa:</strong> ${data.gioMoCua}
                                </div>
                                ` : ''}
                                ${rating > 0 ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>⭐ Đánh giá:</strong> ${rating.toFixed(1)} (${ratingCount} lượt)
                                </div>
                                ` : ''}
                                ${data.dienThoai ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>📞 Điện thoại:</strong> ${data.dienThoai}
                                </div>
                                ` : ''}
                                ${data.website ? `
                                <div class="nearby-place-detail-info-item">
                                    <strong>🌐 Website:</strong> <a href="${data.website}" target="_blank" style="color: var(--color-accent); text-decoration: underline;">${data.website}</a>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    `;

                    // Description
                    if (data.moTa) {
                        html += `
                            <div class="nearby-place-detail-section">
                                <h4>📝 Mô tả</h4>
                                <p class="nearby-place-detail-description">${data.moTa}</p>
                            </div>
                        `;
                    }

                    // Features
                    if (data.dacDiem) {
                        const formattedFeatures = formatJsonToVietnamese(data.dacDiem);
                        if (formattedFeatures) {
                            html += `
                                <div class="nearby-place-detail-section">
                                    <h4>✨ Đặc điểm nổi bật</h4>
                                    <p class="nearby-place-detail-description">${formattedFeatures}</p>
                                </div>
                            `;
                        }
                    }

                    // Amenities
                    if (data.tienNghi) {
                        const formattedAmenities = formatJsonToVietnamese(data.tienNghi);
                        if (formattedAmenities) {
                            html += `
                                <div class="nearby-place-detail-section">
                                    <h4>🏨 Tiện nghi</h4>
                                    <p class="nearby-place-detail-description">${formattedAmenities}</p>
                                </div>
                            `;
                        }
                    }

                    // Additional info from web search
                    if (data.additional_info) {
                        const addInfo = data.additional_info;
                        html += `<div class="nearby-place-detail-section">
                            <h4>🌐 Thông tin bổ sung từ internet</h4>`;
                        
                        if (addInfo.description) {
                            const cleanedDescription = cleanVietnameseText(addInfo.description);
                            html += `<p class="nearby-place-detail-description">${cleanedDescription}</p>`;
                        }
                        
                        if (addInfo.additional_info) {
                            const extra = addInfo.additional_info;
                            html += '<div class="nearby-place-detail-info">';
                            if (extra.best_time_to_visit) {
                                html += `<div class="nearby-place-detail-info-item"><strong>⏰ Thời gian tốt nhất:</strong> ${extra.best_time_to_visit}</div>`;
                            }
                            if (extra.estimated_time) {
                                html += `<div class="nearby-place-detail-info-item"><strong>⏱️ Thời gian tham quan:</strong> ${extra.estimated_time}</div>`;
                            }
                            if (extra.popular_activities) {
                                html += `<div class="nearby-place-detail-info-item"><strong>🎯 Hoạt động phổ biến:</strong> ${extra.popular_activities}</div>`;
                            }
                            html += '</div>';
                        }
                        
                        if (addInfo.reviews_summary) {
                            html += `<p class="nearby-place-detail-description"><strong style="color: var(--color-accent);">Đánh giá tổng hợp:</strong> ${addInfo.reviews_summary}</p>`;
                        }
                        
                        html += `</div>`;
                    }

                    detailPanel.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error loading place info:', error);
                    detailPanel.innerHTML = `
                        <div style="text-align: center; padding: 2rem; color: var(--color-text-light); opacity: 0.8;">
                            <p>Không thể tải thông tin địa điểm. Vui lòng thử lại sau.</p>
                        </div>
                    `;
                });
        }

        // Show place info modal with enriched data (keep for other uses if needed)
        function showPlaceInfo(placeId) {
            const modal = document.getElementById('place-info-modal-overlay');
            const loading = document.getElementById('place-info-loading');
            const content = document.getElementById('place-info-content');
            const title = document.getElementById('place-info-title');
            
            // Show modal
            modal.classList.add('show');
            loading.style.display = 'block';
            content.classList.remove('show');
            
            // Fetch enriched place data
            fetch(`/api/v1/places/${placeId}/enriched/?search_web=true`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Hide loading
                    loading.style.display = 'none';
                    
                    // Populate content
                    title.textContent = data.tenDiaDiem || 'Thông tin địa điểm';
                    
                    // Get image
                    let imageUrl = '';
                    if (data.hinhAnhs && data.hinhAnhs.length > 0) {
                        const mainImage = data.hinhAnhs.find(img => img.laChinh) || data.hinhAnhs[0];
                        imageUrl = mainImage.urlHinhAnh || '';
                    }
                    imageUrl = imageUrl || data.hinhAnhChinh || '';
                    
                    const rating = data.danhGiaTrungBinh || 0;
                    const ratingCount = data.soLuotDanhGia || 0;
                    const price = data.giaVe || 0;
                    const priceText = formatPrice(price);
                    const city = data.tenTinhThanh || (data.maTinhThanh && data.maTinhThanh.tenTinhThanh) || 'Chưa xác định';
                    
                    // Build HTML content
                    let html = '';
                    
                    if (imageUrl) {
                        html += `<img src="${imageUrl}" alt="${data.tenDiaDiem}" class="place-info-image">`;
                    }
                    
                    html += `
                        <div class="place-info-section">
                            <h3>📋 Thông tin cơ bản</h3>
                            <div class="place-info-detail">
                                <div class="place-info-detail-item">
                                    <strong>📍 Địa chỉ:</strong> ${data.diaChi || 'Chưa cập nhật'}
                                </div>
                                <div class="place-info-detail-item">
                                    <strong>🏙️ Tỉnh/Thành:</strong> ${city}
                                </div>
                                <div class="place-info-detail-item">
                                    <strong>💰 Giá vé:</strong> ${priceText}
                                </div>
                                <div class="place-info-detail-item">
                                    <strong>🕐 Giờ mở cửa:</strong> ${data.gioMoCua || 'Chưa cập nhật'}
                                </div>
                                <div class="place-info-detail-item">
                                    <strong>⭐ Đánh giá:</strong> ${rating > 0 ? rating.toFixed(1) : 'Chưa có'} (${ratingCount} lượt)
                                </div>
                                ${data.dienThoai ? `<div class="place-info-detail-item"><strong>📞 Điện thoại:</strong> ${data.dienThoai}</div>` : ''}
                                ${data.website ? `<div class="place-info-detail-item"><strong>🌐 Website:</strong> <a href="${data.website}" target="_blank">${data.website}</a></div>` : ''}
                            </div>
                        </div>
                    `;
                    
                    // Description
                    if (data.moTa) {
                        html += `
                            <div class="place-info-section">
                                <h3>📝 Mô tả</h3>
                                <p class="place-info-description">${data.moTa}</p>
                            </div>
                        `;
                    }
                    
                    // Features
                    if (data.dacDiem) {
                        const formattedFeatures = formatJsonToVietnamese(data.dacDiem);
                        if (formattedFeatures) {
                            html += `
                                <div class="place-info-section">
                                    <h3>✨ Đặc điểm nổi bật</h3>
                                    <p class="place-info-description">${formattedFeatures}</p>
                                </div>
                            `;
                        }
                    }
                    
                    // Amenities
                    if (data.tienNghi) {
                        const formattedAmenities = formatJsonToVietnamese(data.tienNghi);
                        if (formattedAmenities) {
                            html += `
                                <div class="place-info-section">
                                    <h3>🏨 Tiện nghi</h3>
                                    <p class="place-info-description">${formattedAmenities}</p>
                                </div>
                            `;
                        }
                    }
                    
                    // Additional info from web search
                    if (data.additional_info) {
                        const addInfo = data.additional_info;
                        html += `<div class="place-info-section">
                            <h3>🌐 Thông tin bổ sung từ internet</h3>
                            <div class="place-info-additional">`;
                        
                        if (addInfo.description) {
                            const cleanedDescription = cleanVietnameseText(addInfo.description);
                            html += `<h4>Mô tả thêm:</h4><p>${cleanedDescription}</p>`;
                        }
                        
                        if (addInfo.additional_info) {
                            const extra = addInfo.additional_info;
                            html += '<div class="place-info-detail">';
                            if (extra.best_time_to_visit) {
                                html += `<div class="place-info-detail-item"><strong>⏰ Thời gian tốt nhất:</strong> ${extra.best_time_to_visit}</div>`;
                            }
                            if (extra.estimated_time) {
                                html += `<div class="place-info-detail-item"><strong>⏱️ Thời gian tham quan:</strong> ${extra.estimated_time}</div>`;
                            }
                            if (extra.popular_activities) {
                                html += `<div class="place-info-detail-item"><strong>🎯 Hoạt động phổ biến:</strong> ${extra.popular_activities}</div>`;
                            }
                            html += '</div>';
                        }
                        
                        if (addInfo.reviews_summary) {
                            html += `<h4>Đánh giá tổng hợp:</h4><p>${addInfo.reviews_summary}</p>`;
                        }
                        
                        html += `</div></div>`;
                    }
                    
                    content.innerHTML = html;
                    content.classList.add('show');
                })
                .catch(error => {
                    console.error('Error loading place info:', error);
                    loading.innerHTML = '<p style="color: #dc3545;">Không thể tải thông tin địa điểm. Vui lòng thử lại sau.</p>';
                });
        }

        // Close place info modal
        const placeInfoClose = document.getElementById('place-info-close');
        const placeInfoOverlay = document.getElementById('place-info-modal-overlay');
        
        if (placeInfoClose) {
            placeInfoClose.addEventListener('click', () => {
                placeInfoOverlay.classList.remove('show');
            });
        }
        
        if (placeInfoOverlay) {
            placeInfoOverlay.addEventListener('click', (e) => {
                if (e.target === placeInfoOverlay) {
                    placeInfoOverlay.classList.remove('show');
                }
            });
        }
        
        // Close modal with ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && placeInfoOverlay.classList.contains('show')) {
                placeInfoOverlay.classList.remove('show');
            }
        });

        // Smooth scrolling với easing tốt hơn
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    const offset = 80; // Offset cho navbar
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Navbar luôn hiển thị, không shrink
        // (Đã được CSS xử lý: transform: translateY(0) !important)

        // Autocomplete setup
        let autocompleteTimeout = null;
        
        function setupAutocomplete(inputId, dropdownId, locationType) {
            const input = document.getElementById(inputId);
            const dropdown = document.getElementById(dropdownId);
            
            if (!input || !dropdown) return;
            
            let selectedIndex = -1;
            let suggestions = [];
            
            input.addEventListener('input', function(e) {
                const query = e.target.value.trim();
                clearTimeout(autocompleteTimeout);
                
                if (query.length < 1) {
                    dropdown.classList.remove('show');
                    return;
                }
                
                autocompleteTimeout = setTimeout(async () => {
                    try {
                        const response = await fetch(`/api/v1/locations/suggestions/?q=${encodeURIComponent(query)}&type=${locationType}&limit=10`);
                        const data = await response.json();
                        suggestions = data.suggestions || [];
                        selectedIndex = -1;
                        renderSuggestions();
                    } catch (error) {
                        console.error('Autocomplete error:', error);
                        dropdown.classList.remove('show');
                    }
                }, 300);
            });
            
            input.addEventListener('keydown', function(e) {
                if (!dropdown.classList.contains('show') || suggestions.length === 0) return;
                
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
                    updateSelection();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, -1);
                    updateSelection();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (selectedIndex >= 0 && suggestions[selectedIndex]) {
                        selectSuggestion(suggestions[selectedIndex]);
                    }
                } else if (e.key === 'Escape') {
                    dropdown.classList.remove('show');
                }
            });
            
            input.addEventListener('blur', function() {
                setTimeout(() => {
                    dropdown.classList.remove('show');
                }, 200);
            });
            
            function renderSuggestions() {
                if (suggestions.length === 0) {
                    dropdown.classList.remove('show');
                    return;
                }
                
                dropdown.innerHTML = suggestions.map((suggestion, index) => {
                    const queryLower = input.value.trim().toLowerCase();
                    const suggestionLower = suggestion.toLowerCase();
                    const startIdx = suggestionLower.indexOf(queryLower);
                    if (startIdx === -1) {
                        return `<div class="autocomplete-item ${index === selectedIndex ? 'selected' : ''}" data-index="${index}">${suggestion}</div>`;
                    }
                    const before = suggestion.substring(0, startIdx);
                    const match = suggestion.substring(startIdx, startIdx + queryLower.length);
                    const after = suggestion.substring(startIdx + queryLower.length);
                    return `<div class="autocomplete-item ${index === selectedIndex ? 'selected' : ''}" data-index="${index}">${before}<strong>${match}</strong>${after}</div>`;
                }).join('');
                
                dropdown.classList.add('show');
                
                dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
                    item.addEventListener('click', function() {
                        const index = parseInt(this.getAttribute('data-index'));
                        selectSuggestion(suggestions[index]);
                    });
                });
            }
            
            function updateSelection() {
                dropdown.querySelectorAll('.autocomplete-item').forEach((item, index) => {
                    if (index === selectedIndex) {
                        item.classList.add('selected');
                        item.scrollIntoView({ block: 'nearest' });
                    } else {
                        item.classList.remove('selected');
                    }
                });
            }
            
            function selectSuggestion(suggestion) {
                input.value = suggestion;
                dropdown.classList.remove('show');
                suggestions = [];
            }
        }
        
        // Setup autocomplete
        if (document.getElementById('departure-input')) {
            setupAutocomplete('departure-input', 'departure-autocomplete', 'departure');
        }
        if (document.getElementById('destination-input')) {
            setupAutocomplete('destination-input', 'destination-autocomplete', 'destination');
        }
        
        // Geolocation
        const useCurrentLocationBtn = document.getElementById('use-current-location-btn');
        const departureInput = document.getElementById('departure-input');
        
        if (useCurrentLocationBtn && departureInput) {
            useCurrentLocationBtn.addEventListener('click', async function() {
                if (!navigator.geolocation) {
                    alert('Trình duyệt của bạn không hỗ trợ định vị.');
                    return;
                }
                
                this.classList.add('loading');
                this.disabled = true;
                
                navigator.geolocation.getCurrentPosition(
                    async function(position) {
                        const { latitude, longitude } = position.coords;
                        try {
                            const response = await fetch(`/api/v1/locations/reverse-geocode/?lat=${latitude}&lon=${longitude}`);
                            const data = await response.json();
                            if (data.location) {
                                departureInput.value = data.location;
                            } else {
                                throw new Error('Không tìm thấy địa chỉ');
                            }
                        } catch (error) {
                            console.error('Reverse geocode error:', error);
                            alert('Không thể xác định vị trí. Vui lòng nhập thủ công.');
                        } finally {
                            useCurrentLocationBtn.classList.remove('loading');
                            useCurrentLocationBtn.disabled = false;
                        }
                    },
                    function(error) {
                        alert('Không thể lấy vị trí. Vui lòng nhập thủ công.');
                        useCurrentLocationBtn.classList.remove('loading');
                        useCurrentLocationBtn.disabled = false;
                    },
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            });
        }
        
        // Date validation - max 14 days
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        const daysInfo = document.getElementById('days-info');
        
        if (startDateInput && endDateInput && daysInfo) {
            const today = new Date().toISOString().split('T')[0];
            startDateInput.setAttribute('min', today);
            endDateInput.setAttribute('min', today);
            
            function updateDaysValidation() {
                if (!startDateInput.value || !endDateInput.value) {
                    daysInfo.textContent = '';
                    return;
                }
                
                const startDate = new Date(startDateInput.value);
                const endDate = new Date(endDateInput.value);
                
                if (endDate < startDate) {
                    daysInfo.textContent = '⚠️ Ngày về phải sau ngày đi';
                    daysInfo.style.color = '#DC2626';
                    return;
                }
                
                const diffTime = endDate - startDate;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
                
                if (diffDays > 14) {
                    const maxDate = new Date(startDate);
                    maxDate.setDate(maxDate.getDate() + 13);
                    endDateInput.value = maxDate.toISOString().split('T')[0];
                    daysInfo.textContent = `⚠️ Đã điều chỉnh: ${diffDays} → 14 ngày`;
                    daysInfo.style.color = '#F59E0B';
                } else {
                    daysInfo.textContent = `📅 ${diffDays} ngày`;
                    daysInfo.style.color = '#4B5563';
                }
            }
            
            startDateInput.addEventListener('change', function() {
                if (startDateInput.value) {
                    const startDate = new Date(startDateInput.value);
                    const maxDate = new Date(startDate);
                    maxDate.setDate(maxDate.getDate() + 13);
                    endDateInput.setAttribute('min', startDateInput.value);
                    endDateInput.setAttribute('max', maxDate.toISOString().split('T')[0]);
                }
                updateDaysValidation();
            });
            
            endDateInput.addEventListener('change', updateDaysValidation);
        }

        // Form submission với validation
        const tripForm = document.getElementById('tripForm');
        if (tripForm) {
            tripForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Simple validation
                const tripName = document.getElementById('tripName').value;
                const departure = document.getElementById('departure-input').value;
                const destination = document.getElementById('destination-input').value;
                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;
                const travelType = document.getElementById('travelType').value;
                const people = document.getElementById('people').value;

                if (!tripName || !departure || !destination || !startDate || !endDate || !travelType || !people) {
                    alert('Vui lòng điền đầy đủ thông tin!');
                    return;
                }

                const data = {
                    type: 'plan',
                    query_type: 'plan',
                    cities: [destination],
                    start_date: startDate,
                    end_date: endDate,
                    trip_name: tripName,
                    departure_location: departure,
                    group_size: parseInt(people),
                    travel_style: travelType,
                    interests: [travelType]
                };

                console.log('Form data:', data);

                const submitButton = tripForm.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.textContent = '⏳ Đang tạo lịch trình...';
                }

                // Submit to API
                fetch('/api/v1/plan/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken') || ''
                    },
                    credentials: 'include',
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(result => {
                    if (result.status === 'ok') {
                        alert('✅ Lịch trình đã được tạo thành công!');
                        console.log('Itinerary:', result.result);
                    } else {
                        alert('❌ Lỗi: ' + (result.error || 'Không thể tạo lịch trình'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('❌ Lỗi khi gửi dữ liệu');
                })
                .finally(() => {
                    const submitButton = tripForm.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.textContent = '🚀 Tạo lịch trình';
                    }
                });
            });
        }

        // AI Chat Modal - Only initialize if elements exist (for backward compatibility)
        const aiBubble = document.getElementById('ai-bubble');
        const aiChatModal = document.getElementById('ai-chat-modal');
        
        if (aiBubble && aiChatModal) {
            const chatClose = document.getElementById('chat-close');
            const chatSend = document.getElementById('chat-send');
            const chatInput = document.getElementById('chat-input');
            const chatMessages = document.getElementById('chat-messages');

            if (chatClose && chatSend && chatInput && chatMessages) {
                function addMessage(text, isUser = false) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${isUser ? 'user' : 'ai'}`;
                    messageDiv.textContent = text;
                    chatMessages.appendChild(messageDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }

                aiBubble.addEventListener('click', () => {
                    aiChatModal.classList.toggle('open');
                });

                chatClose.addEventListener('click', () => {
                    aiChatModal.classList.remove('open');
                });

                async function sendMessage() {
                    const message = chatInput.value.trim();
                    if (!message) return;

                    addMessage(message, true);
                    chatInput.value = '';
                    chatSend.disabled = true;
                    chatSend.textContent = 'Đang gửi...';

                    try {
                        // Gọi RAG API
                        const response = await fetch('/api/v1/chat/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')
                            },
                            body: JSON.stringify({
                                message: message
                            })
                        });

                        const data = await response.json();

                        if (response.ok && data.status === 'success') {
                            addMessage(data.message, false);
                            
                            // Hiển thị sources nếu có
                            if (data.sources && data.sources.length > 0) {
                                const sourcesText = 'Nguồn tham khảo: ' + data.sources.map(s => s.name).join(', ');
                                addMessage(sourcesText, false);
                            }
                        } else {
                            addMessage(data.error || 'Có lỗi xảy ra. Vui lòng thử lại.', false);
                        }
                    } catch (error) {
                        console.error('Chat error:', error);
                        addMessage('Lỗi kết nối. Vui lòng kiểm tra kết nối mạng và thử lại.', false);
                    } finally {
                        chatSend.disabled = false;
                        chatSend.textContent = 'Gửi';
                    }
                }

                chatSend.addEventListener('click', sendMessage);
                chatInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
            }
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

        // User dropdown and logout modal are handled by navbar.js
        // No need to duplicate the code here

        // Load places when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                loadPopularPlaces();
                loadNearbyPlaces();
            });
        } else {
            loadPopularPlaces();
            loadNearbyPlaces();
        }

        /* ===================================
         * SCROLL ANIMATIONS
         * =================================== */
        
        // Check if user prefers reduced motion
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        // Scroll animation handler
        function handleScrollAnimations() {
            if (prefersReducedMotion) {
                // Skip animations if user prefers reduced motion
                return;
            }
            
            const scrollElements = document.querySelectorAll('.scroll-animate');
            const elementInView = (el, offset = 100) => {
                const elementTop = el.getBoundingClientRect().top;
                return (
                    elementTop <= 
                    (window.innerHeight || document.documentElement.clientHeight) - offset
                );
            };
            
            scrollElements.forEach((el) => {
                if (elementInView(el, 100)) {
                    el.classList.add('animate');
                }
            });
        }
        
        // Throttle scroll event for performance
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (scrollTimeout) {
                window.cancelAnimationFrame(scrollTimeout);
            }
            scrollTimeout = window.requestAnimationFrame(handleScrollAnimations);
        });
        
        // Run once on page load
        handleScrollAnimations();