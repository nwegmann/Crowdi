function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const activeTabButton = document.querySelector(`.tab[data-tab="${tabName}"]`);
    if (activeTabButton) {
        activeTabButton.classList.add('active');
    }

    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Save active tab to localStorage
    localStorage.setItem('activeTab', tabName);
}

// On page load
document.addEventListener('DOMContentLoaded', function () {
    const savedTab = localStorage.getItem('activeTab');
    if (savedTab) {
        switchTab(savedTab);
    } else {
        const firstTabButton = document.querySelector('.tab');
        if (firstTabButton) {
            const defaultTabName = firstTabButton.getAttribute('data-tab');
            switchTab(defaultTabName);
        }
    }

    // Make all tab buttons listen for clicks
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function (e) {
            e.preventDefault();
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });

    document.addEventListener('click', function (e) {
        if (e.target && e.target.matches('.reset-filter')) {
            e.preventDefault(); // prevent any form submit behavior

            const activeButton = document.querySelector('.tab.active');
            const activeTab = activeButton ? activeButton.getAttribute('data-tab') : 'borrow';

            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.value = '';
            }

            const newUrl = new URL(window.location.origin);
            newUrl.pathname = "/";
            newUrl.searchParams.set("tab", activeTab);

            window.location.href = newUrl.toString();
        }
    });
});