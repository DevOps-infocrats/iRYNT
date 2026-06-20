from openpyxl.worksheet.datavalidation import DataValidation

dv1 = DataValidation(type="list", formula1="DropdownData!$A$2:$A$5")
print("Default initialization:")
print("  showDropDown:", dv1.showDropDown)
print("  hide_drop_down:", dv1.hide_drop_down)

dv2 = DataValidation(type="list", formula1="DropdownData!$A$2:$A$5", showDropDown=True)
print("\nWith showDropDown=True:")
print("  showDropDown:", dv2.showDropDown)
print("  hide_drop_down:", dv2.hide_drop_down)

dv3 = DataValidation(type="list", formula1="DropdownData!$A$2:$A$5", showDropDown=False)
print("\nWith showDropDown=False:")
print("  showDropDown:", dv3.showDropDown)
print("  hide_drop_down:", dv3.hide_drop_down)
