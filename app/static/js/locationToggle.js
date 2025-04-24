export function setupLocationToggle(radioName, manualId, latId, lonId) {
    const radios = document.querySelectorAll(`input[name="${radioName}"]`);
    const manualField = document.getElementById(manualId);

    radios.forEach(radio => {
        radio.addEventListener('change', function () {
            if (this.value === 'manual') {
                manualField.style.display = 'block';
                setTimeout(() => {
                    if (window.requestMap) window.requestMap.invalidateSize();
                    if (window.itemMap) window.itemMap.invalidateSize();
                }, 100);
            } else {
                manualField.style.display = 'none';
            }
        });
    });

    // Try to set GPS location on load
    navigator.geolocation.getCurrentPosition(
        function (pos) {
            document.getElementById(latId).value = pos.coords.latitude;
            document.getElementById(lonId).value = pos.coords.longitude;
        },
        function (err) {
            console.error("Geolocation error:", err);
        }
    );
}