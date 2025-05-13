document.addEventListener('DOMContentLoaded', () => {
    // 1) Read the cities dictionary only once
    const jsonTag = document.getElementById('cities-json');
    if (!jsonTag) {
        console.warn('cities-json script tag not found.');
        return;
    }

    let cityData;
    try {
        cityData = JSON.parse(jsonTag.textContent);
    } catch (err) {
        console.error('Could not parse cities JSON:', err);
        return;
    }

    // 2) Attach behaviour to each <select class="city-select">
    document.querySelectorAll('.city-select').forEach(select => {
        const form = select.closest('form');
        const latInput = form.querySelector('input[name="latitude"]');
        const lonInput = form.querySelector('input[name="longitude"]');

        if (!latInput || !lonInput) {
            console.warn('Missing hidden latitude/longitude inputs in form:', form);
            return;
        }

        function setCoords() {
            const coords = cityData[select.value] || {};
            latInput.value = coords.lat ?? coords.latitude ?? '';
            lonInput.value = coords.lng ?? coords.lon ?? coords.longitude ?? '';
        }

        // update on change
        select.addEventListener('change', setCoords);

        // update immediately if a city is pre‑selected
        if (select.value) setCoords();
    });

    // File input handling
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(input => {
        input.addEventListener('change', function (e) {
            const fileName = e.target.files[0]?.name || 'No file selected';
            const fileNameDiv = document.getElementById(input.id + '-request' === 'image-upload-request' ? 'file-name-request' : 'file-name');
            if (fileNameDiv) {
                fileNameDiv.textContent = fileName;
            }
        });
    });
});