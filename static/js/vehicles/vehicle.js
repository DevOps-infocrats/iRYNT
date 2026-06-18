import { initHierarchyControls } from './hierarchy.js';
import { attachValidation } from './validations.js';

export default function initVehiclePage() {
    if (window.jQuery && window.jQuery.fn.select2) {
        window.jQuery('.select2').select2({
            width: '100%',
            theme: 'bootstrap-5',
            placeholder: 'Select',
            allowClear: false,
            // Append dropdown to body to avoid clipping inside overflow: hidden containers
            dropdownParent: window.jQuery(document.body),
            // Hide the search box and show the full options list on click
            minimumResultsForSearch: Infinity,
            // Let Select2 calculate dropdown width automatically when appended to body
            dropdownAutoWidth: true,
        });
    }

    initHierarchyControls({
        companySelector: '#companySelect',
        circleSelector: '#circleSelect',
        clientSelector: '#clientSelect',
        projectSelector: '#projectSelect',
        subzoneSelector: '#subzoneSelect',
        previewCompany: '#previewCompany',
        previewCircle: '#previewCircle',
        previewClient: '#previewClient',
        previewProject: '#previewProject',
        previewSubzone: '#previewSubzone',
        ajaxUrls: {
            circles: '/vehicles/ajax/circles',
            clients: '/vehicles/ajax/clients',
            projects: '/vehicles/ajax/projects',
            subzones: '/vehicles/ajax/subzones',
        },
    });
    attachValidation('#vehicleNumber', {
        checkUrl: '/vehicles/ajax/check-number',
        companySelector: '#companySelect',
        circleSelector: '#circleSelect',
        clientSelector: '#clientSelect',
        projectSelector: '#projectSelect',
        subzoneSelector: '#subzoneSelect',
    });
}
