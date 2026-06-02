/**
 * Shared Navbar JavaScript
 * Handles theme switching, floating/solid navbar states, the mobile drawer,
 * the account dropdown, and the logout confirmation modal.
 */

(function () {
    "use strict";

    const storageKey = "vivu-theme";
    const root = document.documentElement;
    const body = document.body;
    const navbar = document.getElementById("navbar");
    const navMode = body?.dataset?.navMode || "solid";
    const mobileToggle = document.getElementById("mobile-menu-toggle");
    const mobileClose = document.getElementById("mobile-menu-close");
    const mobileOverlay = document.getElementById("mobile-menu-overlay");
    const mobileDrawer = document.getElementById("mobile-drawer");
    const userAvatarBtn = document.getElementById("user-avatar-btn");
    const userDropdownMenu = document.getElementById("user-dropdown-menu");
    const dropdownLogoutLink = document.getElementById("dropdown-logout-link");
    const drawerLogoutLink = document.getElementById("drawer-logout-link");
    const logoutModal = document.getElementById("logout-modal-overlay");
    const logoutModalCancel = document.getElementById("logout-modal-cancel");
    const logoutForm = document.getElementById("logout-form");
    const themeToggleButtons = document.querySelectorAll("#theme-toggle-desktop, #theme-toggle-mobile-top, #theme-toggle-drawer");

    function currentTheme() {
        return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    }

    function getThemeIconMarkup(theme) {
        if (theme === "dark") {
            return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><circle cx="12" cy="12" r="4.5"></circle><path d="M12 2.5v2.2"></path><path d="M12 19.3v2.2"></path><path d="M4.93 4.93l1.56 1.56"></path><path d="M17.51 17.51l1.56 1.56"></path><path d="M2.5 12h2.2"></path><path d="M19.3 12h2.2"></path><path d="M4.93 19.07l1.56-1.56"></path><path d="M17.51 6.49l1.56-1.56"></path></svg>';
        }

        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><path d="M21 12.8A8.8 8.8 0 1 1 11.2 3a7.1 7.1 0 0 0 9.8 9.8Z"></path></svg>';
    }

    function syncThemeIcons(theme) {
        themeToggleButtons.forEach((button) => {
            const icon = button.querySelector(".theme-toggle-icon");
            if (!icon) {
                return;
            }

            icon.innerHTML = getThemeIconMarkup(theme);
            button.setAttribute("aria-label", theme === "dark" ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối");
        });
    }

    function applyTheme(theme, options = {}) {
        const { persist = true } = options;

        root.setAttribute("data-theme", theme);
        root.classList.toggle("dark", theme === "dark");
        root.style.colorScheme = theme;

        if (body) {
            body.setAttribute("data-theme", theme);
            body.classList.toggle("dark", theme === "dark");
        }

        if (persist) {
            localStorage.setItem(storageKey, theme);
        }

        syncThemeIcons(theme);
        window.dispatchEvent(new CustomEvent("vivu:themechange", { detail: { theme } }));
    }

    function toggleTheme() {
        applyTheme(currentTheme() === "dark" ? "light" : "dark");
    }

    function setNavbarState() {
        if (!navbar) {
            return;
        }

        const scrolled = window.pageYOffset > 16;
        navbar.classList.toggle("nav-scrolled", scrolled || navMode !== "floating");
        navbar.classList.toggle("nav-solid", scrolled || navMode !== "floating");
        navbar.classList.toggle("nav-floating", navMode === "floating" && !scrolled);
        navbar.style.boxShadow = "none";
    }

    function openDrawer() {
        if (!mobileDrawer || !mobileOverlay) {
            return;
        }

        mobileDrawer.classList.remove("translate-x-full", "pointer-events-none", "opacity-0");
        mobileOverlay.classList.remove("pointer-events-none", "opacity-0");
        mobileOverlay.classList.add("pointer-events-auto", "opacity-100");
        body.classList.add("drawer-open");
        if (mobileToggle) {
            mobileToggle.setAttribute("aria-expanded", "true");
        }
    }

    function closeDrawer() {
        if (!mobileDrawer || !mobileOverlay) {
            return;
        }

        mobileDrawer.classList.add("translate-x-full", "pointer-events-none", "opacity-0");
        mobileOverlay.classList.add("pointer-events-none", "opacity-0");
        mobileOverlay.classList.remove("pointer-events-auto", "opacity-100");
        body.classList.remove("drawer-open");
        if (mobileToggle) {
            mobileToggle.setAttribute("aria-expanded", "false");
        }
    }

    function toggleUserDropdown(forceOpen) {
        if (!userAvatarBtn || !userDropdownMenu) {
            return;
        }

        const shouldOpen = typeof forceOpen === "boolean"
            ? forceOpen
            : userDropdownMenu.classList.contains("hidden") || userDropdownMenu.classList.contains("invisible");

        if (shouldOpen) {
            userDropdownMenu.classList.remove("hidden", "invisible", "opacity-0", "translate-y-2");
            userDropdownMenu.classList.add("opacity-100", "translate-y-0");
            userAvatarBtn.setAttribute("aria-expanded", "true");
        } else {
            userDropdownMenu.classList.add("invisible", "opacity-0", "translate-y-2");
            userDropdownMenu.classList.remove("opacity-100", "translate-y-0");
            userAvatarBtn.setAttribute("aria-expanded", "false");
        }
    }

    function showLogoutModal() {
        if (!logoutModal) {
            return;
        }

        logoutModal.classList.remove("hidden");
        logoutModal.classList.add("flex");
        toggleUserDropdown(false);
        closeDrawer();
    }

    function hideLogoutModal() {
        if (!logoutModal) {
            return;
        }

        logoutModal.classList.add("hidden");
        logoutModal.classList.remove("flex");
    }

    window.showLogoutModal = showLogoutModal;
    window.hideLogoutModal = hideLogoutModal;

    applyTheme(currentTheme(), { persist: false });
    setNavbarState();
    window.addEventListener("scroll", setNavbarState);

    themeToggleButtons.forEach((button) => {
        button.addEventListener("click", toggleTheme);
    });

    if (window.matchMedia) {
        const media = window.matchMedia("(prefers-color-scheme: dark)");
        media.addEventListener("change", function (event) {
            if (!localStorage.getItem(storageKey)) {
                applyTheme(event.matches ? "dark" : "light", { persist: false });
            }
        });
    }

    if (mobileToggle) {
        mobileToggle.addEventListener("click", openDrawer);
    }
    if (mobileClose) {
        mobileClose.addEventListener("click", closeDrawer);
    }
    if (mobileOverlay) {
        mobileOverlay.addEventListener("click", closeDrawer);
    }

    document.querySelectorAll(".mobile-drawer-link").forEach((link) => {
        link.addEventListener("click", closeDrawer);
    });

    if (userAvatarBtn && userDropdownMenu) {
        userAvatarBtn.addEventListener("click", function (event) {
            event.stopPropagation();
            toggleUserDropdown();
        });

        document.addEventListener("click", function (event) {
            if (!userAvatarBtn.contains(event.target) && !userDropdownMenu.contains(event.target)) {
                toggleUserDropdown(false);
            }
        });
    }

    if (dropdownLogoutLink) {
        dropdownLogoutLink.addEventListener("click", function (event) {
            event.preventDefault();
            showLogoutModal();
        });
    }

    if (drawerLogoutLink) {
        drawerLogoutLink.addEventListener("click", function (event) {
            event.preventDefault();
            showLogoutModal();
        });
    }

    if (logoutModalCancel) {
        logoutModalCancel.addEventListener("click", hideLogoutModal);
    }

    if (logoutModal) {
        logoutModal.addEventListener("click", function (event) {
            if (event.target === logoutModal) {
                hideLogoutModal();
            }
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDrawer();
            hideLogoutModal();
            toggleUserDropdown(false);
        }
    });

    if (logoutForm) {
        logoutForm.addEventListener("submit", function () {
            hideLogoutModal();
        });
    }
})();
