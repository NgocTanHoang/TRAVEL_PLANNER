/**
 * Shared Navbar JavaScript
 * Handles dropdown menus, mobile menu, and logout modal
 */

(function() {
    'use strict';

    // Navbar scroll effect
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            if (currentScroll > 50) {
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
            navMenu.classList.toggle('mobile-open');
            const isExpanded = navMenu.classList.contains('mobile-open');
            mobileMenuToggle.setAttribute('aria-expanded', isExpanded);
        });
    }

    // Search Dropdown Toggle (click và hover)
    const searchDropdown = document.querySelector('.search-dropdown');
    const searchToggle = document.querySelector('.search-toggle');
    const searchDropdownMenu = document.querySelector('.search-dropdown-menu');
    
    if (searchToggle && searchDropdownMenu) {
        // Click để toggle dropdown
        searchToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            searchDropdown.classList.toggle('active');
        });
        
        // Đóng dropdown khi click bên ngoài
        document.addEventListener('click', function(e) {
            if (searchDropdown && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.remove('active');
            }
        });
        
        // Hover vào dropdown để giữ mở
        searchDropdown.addEventListener('mouseenter', function() {
            searchDropdown.classList.add('active');
        });
        
        searchDropdown.addEventListener('mouseleave', function() {
            // Chỉ đóng khi không hover (hover tự động được CSS xử lý)
            setTimeout(() => {
                if (!searchDropdown.matches(':hover')) {
                    searchDropdown.classList.remove('active');
                }
            }, 200);
        });
    }

    // User Avatar Dropdown Toggle
    const userAvatarBtn = document.getElementById('user-avatar-btn');
    const userDropdownMenu = document.getElementById('user-dropdown-menu');
    
    if (userAvatarBtn && userDropdownMenu) {
        userAvatarBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isExpanded = userDropdownMenu.classList.contains('show');
            
            if (isExpanded) {
                userDropdownMenu.classList.remove('show');
                userAvatarBtn.setAttribute('aria-expanded', 'false');
            } else {
                userDropdownMenu.classList.add('show');
                userAvatarBtn.setAttribute('aria-expanded', 'true');
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userAvatarBtn.contains(e.target) && !userDropdownMenu.contains(e.target)) {
                userDropdownMenu.classList.remove('show');
                userAvatarBtn.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close dropdown when clicking on menu items
        const dropdownItems = userDropdownMenu.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            if (!item.id.includes('logout')) {
                item.addEventListener('click', function() {
                    userDropdownMenu.classList.remove('show');
                    userAvatarBtn.setAttribute('aria-expanded', 'false');
                });
            }
        });
    }
    
    // Logout modal logic
    const dropdownLogoutLink = document.getElementById('dropdown-logout-link');
    const logoutModal = document.getElementById('logout-modal');
    const logoutModalOverlay = document.getElementById('logout-modal-overlay');
    const logoutCancel = document.getElementById('logout-cancel');
    const logoutModalCancel = document.getElementById('logout-modal-cancel');
    const logoutForm = document.getElementById('logout-form');
    
    // Function to show logout modal
    function showLogoutModal() {
        // Try logout-modal-overlay first (index.html style)
        const modalOverlay = document.getElementById('logout-modal-overlay');
        // Try logout-modal (base.html style)
        const modal = document.getElementById('logout-modal');
        
        if (modalOverlay) {
            modalOverlay.style.display = 'flex';
            modalOverlay.classList.add('show');
        } else if (modal) {
            modal.style.display = 'flex';
        }
        
        // Close dropdown menu when opening modal
        if (userDropdownMenu) {
            userDropdownMenu.classList.remove('show');
        }
        if (userAvatarBtn) {
            userAvatarBtn.setAttribute('aria-expanded', 'false');
        }
    }
    
    // Function to hide logout modal
    function hideLogoutModal() {
        const modalOverlay = document.getElementById('logout-modal-overlay');
        const modal = document.getElementById('logout-modal');
        
        if (modalOverlay) {
            modalOverlay.style.display = 'none';
            modalOverlay.classList.remove('show');
        } else if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // Make showLogoutModal globally available
    window.showLogoutModal = showLogoutModal;
    window.hideLogoutModal = hideLogoutModal;
    
    // Handle logout link click
    if (dropdownLogoutLink) {
        dropdownLogoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            showLogoutModal();
        });
    }
    
    // Handle logout cancel button (support both ID styles)
    if (logoutCancel) {
        logoutCancel.addEventListener('click', function() {
            hideLogoutModal();
        });
    }
    if (logoutModalCancel) {
        logoutModalCancel.addEventListener('click', function() {
            hideLogoutModal();
        });
    }
    
    // Close modal when clicking overlay
    if (logoutModalOverlay) {
        logoutModalOverlay.addEventListener('click', function(e) {
            if (e.target === logoutModalOverlay) {
                hideLogoutModal();
            }
        });
    }
    if (logoutModal) {
        logoutModal.addEventListener('click', function(e) {
            if (e.target === logoutModal) {
                hideLogoutModal();
            }
        });
    }
    
    // Close modal with ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideLogoutModal();
        }
    });
    
    // Submit logout form when confirm button is clicked
    if (logoutForm) {
        logoutForm.addEventListener('submit', function(e) {
            // Form will submit naturally with POST method and CSRF token
            // This ensures proper logout and redirect to homepage
        });
    }
})();

