document.addEventListener('DOMContentLoaded', () => {
    const tabEl = document.querySelector('#driverTab');
    if (tabEl) {
        const triggerTabList = [].slice.call(tabEl.querySelectorAll('button[data-bs-toggle="tab"]'));
        triggerTabList.forEach(triggerEl => {
            const tabTrigger = new bootstrap.Tab(triggerEl);
            triggerEl.addEventListener('click', event => {
                event.preventDefault();
                tabTrigger.show();
            });
        });
    }
});
