from flask import Blueprint, request, render_template, jsonify, send_file, current_app, flash, redirect, url_for, session
import io
from flask_login import login_required, current_user

# Import services (to be implemented)
from app.modules.users.services.bulk_import_service import BulkImportService
from app.modules.users.services.import_audit_service import ImportAuditService
from app.modules.users.services.excel_parser_service import ExcelParserService
from app.modules.users.services.validation_service import ValidationService

bulk_import_bp = Blueprint('bulk_import', __name__, url_prefix='/user-management')

def _has_bulk_import_permission():
    """Check if current user has bulk import permission (Super Admin, Corporate Admin, Circle Admin)."""
    allowed_roles = {'Super Admin', 'Corporate Admin', 'Circle Admin'}
    user_roles = [r.name for r in getattr(current_user, 'roles', [])]
    if hasattr(current_user, 'primary_role') and current_user.primary_role:
        user_roles.append(current_user.primary_role.name)
    return any(role in allowed_roles for role in user_roles)

@bulk_import_bp.route('/bulk-import', methods=['GET'])
@login_required
def bulk_import_page():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    # Render the bulk import page (template to be created)
    return render_template('users/bulk_import.html')

@bulk_import_bp.route('/bulk-import/template', methods=['GET'])
@login_required
def download_template():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    parser = ExcelParserService()
    wb_bytes = parser.generate_template()
    return send_file(
        io.BytesIO(wb_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='VIL_User_Import_Template.xlsx'
    )

@bulk_import_bp.route('/bulk-import/validate', methods=['POST'])
@login_required
def validate_upload():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    uploaded_file = request.files.get('file')
    if not uploaded_file:
        return jsonify({'error': 'No file provided'}), 400
    parser = ExcelParserService()
    rows = parser.parse_excel(uploaded_file)
    validator = ValidationService()
    summary, errors = validator.validate(rows)
    # Store parsed rows and errors in session for later import
    session['bulk_import_data'] = {'rows': rows, 'errors': errors}
    return jsonify({'summary': summary, 'errors': errors, 'rows': rows})

@bulk_import_bp.route('/bulk-import/import', methods=['POST'])
@login_required
def import_users():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    data = session.get('bulk_import_data')
    if not data:
        return jsonify({'error': 'No validation data found'}), 400
    rows = data.get('rows', [])
    errors = data.get('errors', [])
    # Determine indices of rows that have errors (row_number is 2-indexed because header occupies row 1)
    error_row_indices = {e['row_number'] - 2 for e in errors}
    valid_rows = [row for idx, row in enumerate(rows) if idx not in error_row_indices]
    import_service = BulkImportService()
    import_result = import_service.import_rows(valid_rows, current_user.id)
    import_result['updated'] = 0  # for compatibility
    # Record audit
    audit_service = ImportAuditService()
    audit_service.record_import(
        importer_id=current_user.id,
        total=len(rows),
        succeeded=import_result.get('created', 0),
        failed=len(errors)
    )
    # Clean up session
    session.pop('bulk_import_data', None)
    return jsonify(import_result)

@bulk_import_bp.route('/bulk-import/error-report', methods=['GET'])
@login_required
def download_error_report():
    if not _has_bulk_import_permission():
        return jsonify({'error': 'Forbidden'}), 403
    data = session.get('bulk_import_data', {})
    errors = data.get('errors', [])
    if not errors:
        return jsonify({'error': 'No errors to report'}), 400
    parser = ExcelParserService()
    wb_bytes = parser.generate_error_report(errors)
    return send_file(
        io.BytesIO(wb_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Bulk_Import_Error_Report.xlsx'
    )
