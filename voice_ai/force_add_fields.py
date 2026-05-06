import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def force_add_fields():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        custom_fields = {
            "Voice AI Telephony Account": [
                {
                    "fieldname": "telephony_trunk_id",
                    "label": "Telephony Trunk ID",
                    "fieldtype": "Data",
                    "insert_after": "account_name"
                }
            ],
            "Voice AI Encounter Queue": [
                {
                    "fieldname": "telephony_trunk_id",
                    "label": "Telephony Trunk ID",
                    "fieldtype": "Data",
                    "read_only": 1,
                    "insert_after": "patient_encounter"
                }
            ]
        }
        create_custom_fields(custom_fields, ignore_validate=True)
        frappe.db.commit()
        print("SUCCESS: Forced fields into UI via Custom Field table")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    force_add_fields()
