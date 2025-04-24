


export function initRequestMap() {
    if (window.requestMapInitialized) return;
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
}

export function initItemMap() {
    if (window.itemMapInitialized) return;
    window.itemMapInitialized = true;

    const mapField = document.getElementById('manual-location-field-item');
    const radios = document.querySelectorAll('input[name="location_mode"]');

    window.itemMap = L.map('item-map').setView([46.8, 8.2], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(window.itemMap);

    let itemMarker;
    window.itemMap.on('click', function (e) {
        const { lat, lng } = e.latlng;
        if (itemMarker) window.itemMap.removeLayer(itemMarker);
        itemMarker = L.marker([lat, lng]).addTo(window.itemMap);
        document.getElementById('lat-item').value = lat;
        document.getElementById('lon-item').value = lng;
    });

    if (document.querySelector('input[name="location_mode"]:checked').value === 'auto') {
        navigator.geolocation.getCurrentPosition(function (pos) {
            const { latitude, longitude } = pos.coords;
            itemMarker = L.marker([latitude, longitude]).addTo(window.itemMap);
            document.getElementById('lat-item').value = latitude;
            document.getElementById('lon-item').value = longitude;
            window.itemMap.setView([latitude, longitude], 12);
        }, function (err) {
            console.error("Geolocation error:", err);
        });
    }

    radios.forEach(radio => {
        radio.addEventListener('change', function () {
            if (this.value === 'manual') {
                mapField.style.display = 'block';
                setTimeout(() => window.itemMap.invalidateSize(), 100);
            } else {
                mapField.style.display = 'none';
            }
        });
    });
}