# Responsive Design & Layout Audit Report

This report evaluates the responsiveness of the VIL frontend system across the mandated device profiles, documenting current bugs, alignment issues, layout reflows, and sidebar interactions.

## 1. Targeted Viewport Resolutions
The following viewport sizes were audited and are targeted for support:
*   **Mobile Small / Portrait**: `320px`, `375px`, `390px`, `414px`
*   **Mobile Medium / Landscape**: `480px`
*   **Tablet Portrait / Landscape**: `768px`, `820px`, `912px`
*   **Desktop Standard / Medium**: `1024px`, `1280px`, `1366px`
*   **Desktop Large / High-Res**: `1440px`, `1600px`, `1920px`

---

## 2. Structural Component Audits
### A. Sidebar Responsiveness
*   **Desktop (>= 992px)**: Sidebar sits fixed on the left with width `260px`. Main page content is offset to the right by `260px`. Smooth transition toggles collapse it to an icon-only style (`70px`).
*   **Tablet (768px - 991px)**: The sidebar defaults to collapsible sidebar, transitioning to `70px` collapsed state automatically. It can be hovered/clicked to expand.
*   **Mobile (< 768px)**: The sidebar transitions to an off-canvas drawer sliding in from the left when clicking the navbar hamburger button. It covers the viewport with an overlay backdrop.
*   **Bugs Identified**: 
    *   No auto-close functionality exists upon clicking link items on mobile, causing the sidebar to block the view even after navigation triggers.
    *   Inconsistent toggle state storage in `localStorage` leads to layout shifts on page reload.
    *   Main content margin-left is hardcoded in pixel-based styles, causing horizontal page overlaps on viewports between 768px and 991px.

### B. Dashboard Responsiveness
*   **Desktop**: Dashboard metrics display 4 cards per row.
*   **Tablet**: Reflows to 2 cards per row.
*   **Mobile**: Reflows to 1 card per row.
*   **Bugs Identified**: 
    *   KPI widgets use hardcoded columns or fixed pixel widths instead of dynamic CSS grid wrappers `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`. This causes cards to clip or overlap on smaller desktop screens (1024px).
    *   In viewports below 360px, metric value numbers overlap with the card's avatar icons.

### C. Form Responsiveness
*   **Desktop**: Multi-column form layouts using Bootstrap grids (e.g. `col-md-6`, `col-lg-4`).
*   **Tablet**: Reflows to 2-column configurations.
*   **Mobile**: Collapses to a single-column layout where all input fields occupy 100% width.
*   **Bugs Identified**:
    *   Buttons at the bottom of forms (e.g. Save, Reset, Cancel) are positioned using float-right classes or hardcoded absolute flex alignments. On mobile screens (< 480px), they wrap awkwardly, overflow their parent cards, or stack without spacing.
    *   Labels and input boxes become misaligned on tablet profiles because input labels are set to fixed inline widths on some forms (e.g. circles and projects edit pages).

### D. Table Data Grid Responsiveness
*   **Desktop**: Normal multi-column table listing fields (IDs, names, dates, actions).
*   **Tablet**: Wraps columns inside standard scrollable tables.
*   **Mobile**: In viewports < 768px, traditional wide tables overflow the page container, causing horizontal scrollbars on the entire page.
*   **Proposed Target Solution**: All data grids must wrap inside a `.table-responsive` block wrapper, and columns must use explicit width restrictions or flex styling. For mobile viewports (< 576px), tables should reflow into card-based layouts where each row is represented as a self-contained card containing key-value data fields and action buttons to preserve ease of navigation.

### E. Geo-Fencing Section Responsiveness
*   **The Issue**: The Geo-Fencing config panels (Geo-Fencing Enabled toggle, Allowed Radius, Attendance Radius, GPS Validation, Restricted Movement) are styled with custom inline CSS and absolute alignments.
    *   Controls overlap on tablet portrait sizes.
    *   Labels wrap or are hidden on mobile viewports (< 375px).
    *   Toggle switches do not align vertically.
*   **Required Layout System**: Use responsive CSS Grid:
    *   *Desktop (>= 992px)*: 3 columns (Geo-Fencing enabled + allowed radius + attendance radius) on row 1, and 2 columns (GPS validation + restricted movement) on row 2.
    *   *Tablet (768px - 991px)*: 2-column grid layout.
    *   *Mobile (< 768px)*: Single-column stacked grid layout.
    *   *Equal heights, vertical toggle alignment, and standard gap spacing (24px) are mandatory.*
