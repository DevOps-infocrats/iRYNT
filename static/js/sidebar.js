// Store event handler references so we can remove them later
let sidebarEventHandlers = {
    toggleButton: null,
    mobileToggle: null,
    sidebarClick: null,
    documentClick: null,
    escapeKey: null,
    resize: null,
    backdrop: null,
    collapseEvents: []
};

const initDashboardSidebar = () => {
    const sidebar = document.getElementById('dashboardSidebar');
    const toggleButton = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileSidebarToggle');
    const backdrop = document.getElementById('sidebarBackdrop');
    const shell = document.querySelector('.dashboard-shell, .permissions-shell');

    if (!sidebar) {
        return;
    }

    // Remove old event listeners to prevent duplicates
    if (toggleButton && sidebarEventHandlers.toggleButton) {
        toggleButton.removeEventListener('click', sidebarEventHandlers.toggleButton);
    }
    if (mobileToggle && sidebarEventHandlers.mobileToggle) {
        mobileToggle.removeEventListener('click', sidebarEventHandlers.mobileToggle);
    }
    if (sidebarEventHandlers.sidebarClick) {
        sidebar.removeEventListener('click', sidebarEventHandlers.sidebarClick);
    }
    if (sidebarEventHandlers.documentClick) {
        document.removeEventListener('click', sidebarEventHandlers.documentClick);
    }
    if (sidebarEventHandlers.escapeKey) {
        document.removeEventListener('keydown', sidebarEventHandlers.escapeKey);
    }
    if (sidebarEventHandlers.resize) {
        window.removeEventListener('resize', sidebarEventHandlers.resize);
    }
    if (backdrop && sidebarEventHandlers.backdrop) {
        backdrop.removeEventListener('click', sidebarEventHandlers.backdrop);
    }
    // Remove collapse event listeners
    sidebarEventHandlers.collapseEvents.forEach(({ element, handler, eventType }) => {
        element.removeEventListener(eventType, handler);
    });
    sidebarEventHandlers.collapseEvents = [];

    // Detect if we're on mobile or desktop
    const isMobile = () => window.innerWidth <= 991;

    // Restore desktop collapse state from localStorage on load
    const initCollapsedState = () => {
        const collapsed = localStorage.getItem('dashboardSidebarCollapsed') === 'true';
        if (collapsed && !isMobile()) {
            sidebar.classList.add('collapsed');
            shell?.classList.add('sidebar-collapsed');
            document.body.classList.add('sidebar-collapsed');
        } else {
            // Ensure collapsed state is removed if not supposed to be collapsed
            sidebar.classList.remove('collapsed');
            shell?.classList.remove('sidebar-collapsed');
            document.body.classList.remove('sidebar-collapsed');
        }
        updateToggleIcon();
    };

    const updateToggleIcon = () => {
        const icon = toggleButton?.querySelector('span');
        if (!icon) {
            return;
        }
        icon.textContent = sidebar.classList.contains('collapsed') ? 'chevron_right' : 'chevron_left';
    };

    const persistSidebarState = () => {
        const isCollapsed = sidebar.classList.contains('collapsed');
        shell?.classList.toggle('sidebar-collapsed', isCollapsed);
        document.body.classList.toggle('sidebar-collapsed', isCollapsed);
        localStorage.setItem('dashboardSidebarCollapsed', isCollapsed ? 'true' : 'false');
        updateToggleIcon();
    };

    // DESKTOP: Collapse/expand sidebar (NOT overlay)
    const handleDesktopToggle = (event) => {
        event?.preventDefault();
        event?.stopPropagation();
        
        if (isMobile()) {
            return; // Mobile uses drawer, not collapse
        }
        
        const isCurrentlyCollapsed = sidebar.classList.contains('collapsed');
        if (isCurrentlyCollapsed) {
            sidebar.classList.remove('collapsed');
        } else {
            sidebar.classList.add('collapsed');
        }
        persistSidebarState();
    };

    // MOBILE: Open/close drawer overlay (NOT collapse)
    const setMobileDrawerOpen = (isOpen) => {
        if (!isMobile()) {
            return; // Desktop doesn't use drawer
        }

        sidebar.classList.toggle('mobile-open', isOpen);
        backdrop?.classList.toggle('show', isOpen);
        document.body.classList.toggle('sidebar-open', isOpen);
    };

    // Initialize the sidebar with proper state
    initCollapsedState();

    // Desktop collapse button
    if (toggleButton) {
        sidebarEventHandlers.toggleButton = handleDesktopToggle;
        toggleButton.addEventListener('click', handleDesktopToggle);
    }

    // Mobile hamburger menu
    if (mobileToggle) {
        sidebarEventHandlers.mobileToggle = (event) => {
            event?.preventDefault();
            event?.stopPropagation();
            setMobileDrawerOpen(!sidebar.classList.contains('mobile-open'));
        };
        mobileToggle.addEventListener('click', sidebarEventHandlers.mobileToggle);
    }

    // Mobile drawer close on link click
    sidebarEventHandlers.sidebarClick = (event) => {
        const isMobileViewport = window.innerWidth < 768 || isMobile();
        if (!isMobileViewport || !sidebar.classList.contains('mobile-open')) {
            return;
        }
        const targetLink = event.target.closest('.sidebar-nav a');
        if (targetLink) {
            setMobileDrawerOpen(false);
        }
    };
    sidebar.addEventListener('click', sidebarEventHandlers.sidebarClick);

    // Mobile backdrop close
    if (backdrop) {
        sidebarEventHandlers.backdrop = () => setMobileDrawerOpen(false);
        backdrop.addEventListener('click', sidebarEventHandlers.backdrop);
    }

    // Section toggle handlers (for submenu expand/collapse)
    const sectionToggles = Array.from(sidebar.querySelectorAll('.section-toggle'));
    sectionToggles.forEach(toggle => {
        const section = toggle.getAttribute('data-section');
        const targetId = toggle.getAttribute('data-bs-target')?.slice(1);
        const collapseElement = targetId ? document.getElementById(targetId) : null;

        if (!section || !collapseElement) {
            return;
        }

        const savedOpen = localStorage.getItem(`sidebarSection_${section}`);
        const shouldOpen = savedOpen === null ? toggle.classList.contains('active') : savedOpen === 'true';

        collapseElement.classList.toggle('show', shouldOpen);
        toggle.classList.toggle('active', shouldOpen);
        toggle.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
    });

    const syncCollapseState = (collapseElement, isShown) => {
        const toggler = sidebar.querySelector(`[data-bs-target="#${collapseElement.id}"]`);
        if (!toggler) {
            return;
        }

        toggler.classList.toggle('active', isShown);
        toggler.setAttribute('aria-expanded', String(isShown));

        if (toggler.classList.contains('section-toggle')) {
            const section = toggler.getAttribute('data-section');
            if (section) {
                localStorage.setItem(`sidebarSection_${section}`, String(isShown));
            }

            if (isShown) {
                sectionToggles.forEach(otherToggle => {
                    if (otherToggle === toggler) {
                        return;
                    }

                    const otherTargetId = otherToggle.getAttribute('data-bs-target')?.slice(1);
                    const otherCollapse = otherTargetId ? document.getElementById(otherTargetId) : null;
                    if (otherCollapse?.classList.contains('show')) {
                        if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
                            const otherInstance = bootstrap.Collapse.getOrCreateInstance(otherCollapse, { toggle: false });
                            otherInstance.hide();
                        } else {
                            otherCollapse.classList.remove('show');
                            otherToggle.classList.remove('active');
                            otherToggle.setAttribute('aria-expanded', 'false');
                            const otherSection = otherToggle.getAttribute('data-section');
                            if (otherSection) {
                                localStorage.setItem(`sidebarSection_${otherSection}`, 'false');
                            }
                        }
                    }
                });
            }
        }
    };

    if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
        Array.from(sidebar.querySelectorAll('.collapse')).forEach(collapseElement => {
            const onShown = () => syncCollapseState(collapseElement, true);
            const onHidden = () => syncCollapseState(collapseElement, false);
            collapseElement.addEventListener('shown.bs.collapse', onShown);
            collapseElement.addEventListener('hidden.bs.collapse', onHidden);
            sidebarEventHandlers.collapseEvents.push({ element: collapseElement, handler: onShown, eventType: 'shown.bs.collapse' });
            sidebarEventHandlers.collapseEvents.push({ element: collapseElement, handler: onHidden, eventType: 'hidden.bs.collapse' });
        });
    }

    // Close mobile drawer when clicking outside on mobile
    sidebarEventHandlers.documentClick = (event) => {
        if (!isMobile() || !sidebar.classList.contains('mobile-open')) {
            return;
        }
        if (mobileToggle?.contains(event.target) || sidebar.contains(event.target)) {
            return;
        }
        setMobileDrawerOpen(false);
    };
    document.addEventListener('click', sidebarEventHandlers.documentClick);

    // Close mobile drawer on Escape key
    sidebarEventHandlers.escapeKey = (event) => {
        if (event.key === 'Escape' && isMobile() && sidebar.classList.contains('mobile-open')) {
            setMobileDrawerOpen(false);
        }
    };
    document.addEventListener('keydown', sidebarEventHandlers.escapeKey);

    // Handle window resize to reset state when switching between mobile and desktop
    sidebarEventHandlers.resize = () => {
        if (isMobile()) {
            // If transitioning to mobile, close any desktop collapse
            sidebar.classList.remove('collapsed');
            shell?.classList.remove('sidebar-collapsed');
            document.body.classList.remove('sidebar-collapsed');
        } else {
            // If transitioning to desktop, close any mobile drawer
            sidebar.classList.remove('mobile-open');
            backdrop?.classList.remove('show');
            document.body.classList.remove('sidebar-open');
            // Re-initialize collapsed state on desktop based on localStorage
            initCollapsedState();
        }
    };
    window.addEventListener('resize', sidebarEventHandlers.resize);
};

// Call initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardSidebar);
} else {
    initDashboardSidebar();
}

