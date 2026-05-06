import frappe

def production_ui():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        dt = "Voice AI Encounter Queue"
        fieldname = "telephony_trunk_id"
        
        # 1. Update Property Setters to professional values
        # We keep the 'insert_after' and 'hidden: 0' to ensure it stays in place
        properties = [
            {"property": "label", "value": "Telephony Trunk ID", "type": "Data"},
            {"property": "description", "value": "", "type": "Text"},
            {"property": "read_only", "value": "1", "type": "Check"}
        ]
        
        for p in properties:
            frappe.db.set_value("Property Setter", {"doc_type": dt, "field_name": fieldname, "property": p["property"]}, "value", p["value"])
        
        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: Production UI applied.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    production_ui()
