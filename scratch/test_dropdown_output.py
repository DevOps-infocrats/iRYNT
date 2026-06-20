import io
from app import create_app
from app.modules.users.services.excel_parser_service import ExcelParserService
from openpyxl import load_workbook

app = create_app()
with app.app_context():
    service = ExcelParserService()
    template_bytes = service.generate_template()
    
    wb = load_workbook(filename=io.BytesIO(template_bytes))
    ws = wb.active
    
    print("Worksheet Data Validations:")
    for dv in ws.data_validations.dataValidation:
        print("Formula1:", dv.formula1)
        print("Ranges:", dv.sqref)
        print("showDropDown:", dv.showDropDown)
        print("hide_drop_down:", getattr(dv, 'hide_drop_down', None))
        print("allow_blank:", dv.allow_blank)
        print("-" * 30)
