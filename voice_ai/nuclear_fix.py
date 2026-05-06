import frappe

def nuclear_fix():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        dt = "Voice AI Encounter Queue"
        fieldname = "telephony_trunk_id"
        
        # 1. Clear any existing property setters for this field to avoid confusion
        frappe.db.delete("Property Setter", {"doc_type": dt, "field_name": fieldname})
        
        # 2. Force the field to be VISIBLE and EDITABLE via a strong Property Setter
        properties = [
            {"property": "hidden", "value": "0", "type": "Check"},
            {"property": "read_only", "value": "0", "type": "Check"},
            {"property": "label", "value": "TELEPHONY TRUNK ID (LIVE)", "type": "Data"},
            {"property": "description", "value": "Visible for testing", "type": "Text"},
            {"property": "insert_after", "value": "session_id", "type": "Data"}
        ]
        
        for p in properties:
            ps = frappe.get_doc({
                "doctype": "Property Setter",
                "doc_type": dt,
                "field_name": fieldname,
                "property": p["property"],
                "value": p["value"],
                "property_type": p["type"],
                "doctype_or_field": "DocField"
            })
            ps.insert(ignore_permissions=True)
        
        # 3. Clear cache
        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: Nuclear fix applied. Field is now forced to be visible and editable.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    nuclear_fix()
