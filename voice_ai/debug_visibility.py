import frappe
import json

def debug_visibility():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Check Encounter Queue Custom Field
        cf = frappe.db.get_value("Custom Field", {"dt": "Voice AI Encounter Queue", "fieldname": "telephony_trunk_id"}, "*", as_dict=True)
        if cf:
            print(f"Custom Field found: {json.dumps(cf, indent=2, default=str)}")
        else:
            print("Custom Field NOT FOUND in database!")

        # Check for any Property Setters hiding it
        ps = frappe.get_all("Property Setter", filters={"doc_type": "Voice AI Encounter Queue", "field_name": "telephony_trunk_id"})
        print(f"Property Setters for this field: {ps}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    debug_visibility()
