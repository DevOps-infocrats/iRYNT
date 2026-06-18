document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('companyForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const countrySelect = document.getElementById('country_id');
    const stateSelect = document.getElementById('state_id');
    const citySelect = document.getElementById('city_id');
    const countrySearch = document.getElementById('countrySearch');
    const stateSearch = document.getElementById('stateSearch');
    const citySearch = document.getElementById('citySearch');

    const loadSelectOptions = (select, items, selectedId) => {
        select.innerHTML = '<option value="">Choose...</option>';
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.name;
            if (selectedId && selectedId.toString() === item.id.toString()) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    };

    const filterSelect = (select, query) => {
        const options = Array.from(select.options).slice(1);
        const filter = query.trim().toLowerCase();
        options.forEach(option => {
            const visible = option.textContent.toLowerCase().includes(filter);
            option.hidden = !visible;
        });
    };

    const fetchJson = async (url) => {
        const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
        if (!res.ok) {
            throw new Error('Unable to load location data.');
        }
        return res.json();
    };

    const loadCountries = async () => {
        try {
            const data = await fetchJson('/companies/locations/countries');
            const selectedCountry = countrySelect.dataset.selected || '';
            loadSelectOptions(countrySelect, data, selectedCountry);
            if (selectedCountry) {
                await loadStates(selectedCountry);
            }
        } catch (error) {
            console.error(error);
        }
    };

    const loadStates = async (countryId) => {
        try {
            if (!countryId) {
                stateSelect.innerHTML = '<option value="">Choose country first</option>';
                citySelect.innerHTML = '<option value="">Choose state first</option>';
                return;
            }
            const data = await fetchJson(`/companies/locations/states?country_id=${encodeURIComponent(countryId)}`);
            const selectedState = stateSelect.dataset.selected || '';
            loadSelectOptions(stateSelect, data, selectedState);
            if (selectedState) {
                await loadCities(selectedState);
            }
        } catch (error) {
            console.error(error);
        }
    };

    const loadCities = async (stateId) => {
        try {
            if (!stateId) {
                citySelect.innerHTML = '<option value="">Choose state first</option>';
                return;
            }
            const data = await fetchJson(`/companies/locations/cities?state_id=${encodeURIComponent(stateId)}`);
            const selectedCity = citySelect.dataset.selected || '';
            loadSelectOptions(citySelect, data, selectedCity);
        } catch (error) {
            console.error(error);
        }
    };

    if (countrySelect) {
        loadCountries();
    }

    if (countrySelect) {
        countrySelect.addEventListener('change', async () => {
            stateSelect.dataset.selected = '';
            citySelect.dataset.selected = '';
            await loadStates(countrySelect.value);
        });
    }

    if (stateSelect) {
        stateSelect.addEventListener('change', async () => {
            citySelect.dataset.selected = '';
            await loadCities(stateSelect.value);
        });
    }

    if (countrySearch) {
        countrySearch.addEventListener('input', () => filterSelect(countrySelect, countrySearch.value));
    }
    if (stateSearch) {
        stateSearch.addEventListener('input', () => filterSelect(stateSelect, stateSearch.value));
    }
    if (citySearch) {
        citySearch.addEventListener('input', () => filterSelect(citySelect, citySearch.value));
    }

    ['company_code', 'gst_number', 'pan_number'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('blur', () => {
                input.value = input.value.toUpperCase();
            });
        }
    });

    if (form) {
        form.addEventListener('submit', (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
                return;
            }
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';
        });
    }

    const resetButton = document.getElementById('resetButton');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            form.classList.remove('was-validated');
            countrySearch.value = '';
            stateSearch.value = '';
            citySearch.value = '';
            setTimeout(() => {
                if (countrySelect.dataset.selected) {
                    countrySelect.value = countrySelect.dataset.selected;
                }
                if (stateSelect.dataset.selected) {
                    stateSelect.value = stateSelect.dataset.selected;
                }
                if (citySelect.dataset.selected) {
                    citySelect.value = citySelect.dataset.selected;
                }
            }, 0);
        });
    }
});