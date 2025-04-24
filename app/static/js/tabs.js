function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.tab[onclick="switchTab('${tabName}')"]`).classList.add('active');

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const selectedTab = document.getElementById(`${tabName}-tab`);
    selectedTab.classList.add('active');

    if (tabName === 'my-requests') {
        if (!window.requestMapInitialized) {
            const tryInitMap = () => {
                const mapContainer = document.getElementById('request-map');
                if (!mapContainer) {
                    setTimeout(tryInitMap, 100);
                    return;
                }

                window.requestMapInitialized = true;

                const mapField = document.getElementById('manual-location-field-request');
                const radios = document.querySelectorAll('input[name="location_mode"]');

                window.requestMap = L.map('request-map').setView([46.8, 8.2], 8);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; OpenStreetMap contributors'
                }).addTo(window.requestMap);

                let requestMarker;
                window.requestMap.on('click', function (e) {
                    const { lat, lng } = e.latlng;
                    if (requestMarker) window.requestMap.removeLayer(requestMarker);
                    requestMarker = L.marker([lat, lng]).addTo(window.requestMap);
                    document.getElementById('lat-request').value = lat;
                    document.getElementById('lon-request').value = lng;
                });

                if (document.querySelector('input[name="location_mode"]:checked').value === 'auto') {
                    navigator.geolocation.getCurrentPosition(function (pos) {
                        const { latitude, longitude } = pos.coords;
                        requestMarker = L.marker([latitude, longitude]).addTo(window.requestMap);
                        document.getElementById('lat-request').value = latitude;
                        document.getElementById('lon-request').value = longitude;
                        window.requestMap.setView([latitude, longitude], 12);
                    }, function (err) {
                        console.error("Geolocation error:", err);
                    });
                }

                radios.forEach(radio => {
                    radio.addEventListener('change', function () {
                        if (this.value === 'manual') {
                            mapField.style.display = 'block';
                            setTimeout(() => window.requestMap.invalidateSize(), 100);
                        } else {
                            mapField.style.display = 'none';
                        }
                    });
                });
            };

            tryInitMap();
        } else {
            setTimeout(() => {
                window.requestMap.invalidateSize();
            }, 100);
        }
    }
}