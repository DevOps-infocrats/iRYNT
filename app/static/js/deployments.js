document.addEventListener('DOMContentLoaded', () => {
    const vehicleSelect = document.getElementById('vehicle_id');
    const projectSelect = document.getElementById('project_id');
    const subzoneSelect = document.getElementById('subzone_id');
    const driverSelect = document.getElementById('driver_id');

    const fetchJson = async (url) => {
        const response = await fetch(url, {
            headers: { 'Accept': 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`Request failed with status ${response.status}`);
        }
        return response.json();
    };

    const resetSelect = (select, placeholderText) => {
        if (!select) {
            return;
        }
        select.innerHTML = '';
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = placeholderText;
        select.appendChild(placeholder);
        select.value = '';
    };

    const setSelectOptions = (select, options, selectedValue) => {
        if (!select) {
            return;
        }
        select.innerHTML = '';
        options.forEach((optionData) => {
            const option = document.createElement('option');
            option.value = optionData.id;
            option.textContent = optionData.text;
            if (selectedValue && selectedValue.toString() === optionData.id.toString()) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    };

    const loadSubzonesForProject = async (projectId, selectedSubzoneId = '') => {
        if (!subzoneSelect) {
            return;
        }

        if (!projectId) {
            resetSelect(subzoneSelect, 'Select subzone');
            return;
        }

        try {
            const data = await fetchJson(`/deployments/ajax/subzones?project_id=${encodeURIComponent(projectId)}`);
            if (!Array.isArray(data)) {
                resetSelect(subzoneSelect, 'Select subzone');
                return;
            }
            setSelectOptions(subzoneSelect, data, selectedSubzoneId);
        } catch (error) {
            console.error('Unable to load subzones:', error);
            resetSelect(subzoneSelect, 'Select subzone');
        }
    };

    const resetDriverOptions = () => {
        if (!driverSelect) {
            return;
        }
        resetSelect(driverSelect, 'Select driver (optional)');
    };

    const updateDriverOptions = (drivers) => {
        if (!driverSelect) {
            return;
        }
        const options = [{ id: '', text: 'Select driver (optional)' }, ...(Array.isArray(drivers) ? drivers : [])];
        setSelectOptions(driverSelect, options, '');
    };

    const handleVehicleChange = async () => {
        if (!vehicleSelect) {
            return;
        }

        const vehicleId = vehicleSelect.value;
        if (!vehicleId) {
            if (projectSelect) {
                projectSelect.value = '';
            }
            resetSelect(subzoneSelect, 'Select subzone');
            resetDriverOptions();
            return;
        }

        try {
            const data = await fetchJson(`/deployments/ajax/vehicle-info?vehicle_id=${encodeURIComponent(vehicleId)}`);
            if (projectSelect) {
                projectSelect.value = data.project_id || '';
            }
            await loadSubzonesForProject(data.project_id, data.subzone_id);
            updateDriverOptions(data.drivers || []);
        } catch (error) {
            console.error('Unable to load vehicle metadata:', error);
            if (projectSelect) {
                projectSelect.value = '';
            }
            resetSelect(subzoneSelect, 'Select subzone');
            resetDriverOptions();
        }
    };

    if (vehicleSelect) {
        vehicleSelect.addEventListener('change', handleVehicleChange);
    }

    if (projectSelect) {
        projectSelect.addEventListener('change', async () => {
            await loadSubzonesForProject(projectSelect.value);
            resetDriverOptions();
        });
    }

    if (vehicleSelect && vehicleSelect.value) {
        handleVehicleChange();
    }
});
