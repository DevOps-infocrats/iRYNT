# CSS Conflict & Override Audit Report

This report documents specificity pollution, design-token bypasses, hardcoded layout limits, and Bootstrap theme overrides across the VIL stylesheet repository.

## 1. Audit Metrics Summary
*   **Total Custom Stylesheets**: 21
*   **Total Size of Stylesheets**: 122.86 KB
*   **Usage of `!important`**: 92 declarations
*   **Hardcoded HEX Color Codes**: 284 instances
*   **Hardcoded RGB/RGBA Color Codes**: 303 instances
*   **Total Hardcoded Colors**: 587 overrides

---

## 2. Token Compliance Audit
### A. Hardcoded Color Bypasses
Many module CSS files use raw HEX and RGB/RGBA values instead of colors defined in `design-tokens.css`:
*   `static/css/compliance.css`: Contains **30** hardcoded HEX codes (e.g. `#1e293b`, `#f8fafc`) and **1** RGB color.
*   `static/css/roles/roles.css`: Contains **26** hardcoded HEX codes and **15** RGB codes.
*   `static/css/projects/project.css`: Contains **24** hardcoded HEX codes and **16** RGB codes.
*   `static/css/dashboard.css`: Contains **22** HEX codes and **46** RGB codes.
*   `static/css/auth.css`: Contains **19** HEX codes and **34** RGB codes.
*   `static/css/subzones/subzone.css`: Contains **17** HEX codes and **20** RGB codes.
*   `static/css/users/users.css`: Contains **17** HEX codes and **22** RGB codes.

### B. Spacing & Borders
*   Instead of referencing dynamic spacing variables (e.g., `var(--spacing-4)`), stylesheets use static padding values like `padding: 15px 22px;` or margins such as `margin-bottom: 25px;`.
*   Border radii are defined statically (e.g., `border-radius: 10px;`, `border-radius: 14px;`, `border-radius: 22px;`) which violates the centralized radius scale (`--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`).

---

## 3. Specificity & `!important` Usage
A total of **92 occurrences** of `!important` are present in custom CSS files, disrupting normal CSS cascade flow:
*   `static/css/design-tokens.css`: **54** overrides.
*   `static/css/roles/roles.css`: **16** overrides.
*   `static/css/users/users.css`: **8** overrides.
*   `static/css/sidebar.css`: **7** overrides.
*   `static/css/projects/project.css`: **2** overrides.
*   `static/css/subzones/subzone-dashboard.css`: **2** overrides.
*   `static/css/auth.css`: **1** override.
*   `static/css/vehicles/vehicle-dashboard.css`: **1** override.
*   `static/css/vehicles/vehicle-responsive.css`: **1** override.

*Action required*: Refactor elements to rely on CSS specificity selectors, nested namespaces, or Bootstrap CSS variables instead of `!important`.

---

## 4. Hardcoded Dimensions (Widths & Heights)
*   **Input Fields and Dropdowns**: Heights are set using static values like `height: 40px` or `height: 45px` rather than enforcing the global input standard height of `48px`.
*   **Cards and Panels**: Widths are locked in pixels (e.g. `width: 320px;`, `max-width: 420px;`), preventing cards from fluidly reflowing inside fluid flex containers or grid columns.
*   **KPI Cards**: Fixed card heights are defined on desktop dashboard layouts. When wrapped to smaller dimensions, content overflows the card limits.

---

## 5. Bootstrap Selector Overrides
Stylesheets directly target global Bootstrap namespace selectors without specific class constraints:
*   `body` and `html` margins are altered in module-specific styles.
*   `.btn` padding, border-radius, background, and shadows are modified globally in `sidebar.css`, `dashboard.css`, and `auth.css`, overriding default Bootstrap hover states.
*   `.card` background-color and shadows are overridden per-module, resulting in different border styling across companies, circles, and clients views.
*   `.table` borders, zebra stripes, and cell paddings are globally modified in `client.css` and `company.css` instead of introducing standard VIL component wrappers (e.g., `.vil-table`).
*   `.form-control` and `.form-select` inputs have custom line heights and border colors overridden locally, which bypasses global input styling consistency.
