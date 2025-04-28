function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const activeTab = document.querySelector(`.tab[onclick="switchTab('${tabName}')"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Save active tab to localStorage
    localStorage.setItem('activeTab', tabName);
}

// On page load, restore the active tab
document.addEventListener('DOMContentLoaded', function () {
    const savedTab = localStorage.getItem('activeTab');
    if (savedTab) {
        switchTab(savedTab);
    } else {
        // Default to first tab
        const firstTabButton = document.querySelector('.tab');
        if (firstTabButton) {
            const defaultTabName = firstTabButton.getAttribute('onclick').match(/switchTab\('(.+)'\)/)[1];
            switchTab(defaultTabName);
        }
    }
});

document.getElementById('reset-filter').addEventListener('click', function () {
    // Clear the search input field
    document.querySelector('input[name="search"]').value = '';

    // Reload the page to reset the filter and show all items
    window.location.href = '/';
});