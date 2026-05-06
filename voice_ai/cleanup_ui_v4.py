import frappe

def cleanup_ui():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        dt = "Voice AI Encounter Queue"
        
        # 1. Hide unwanted fields
        fields_to_hide = ["order_id", "customer_name", "external_queue_id"]
        for fieldname in fields_to_hide:
            frappe.db.delete("Property Setter", {"doc_type": dt, "field_name": fieldname, "property": "hidden"})
            
            ps = frappe.get_doc({
                "doctype": "Property Setter",
                "doc_type": dt,
                "doctype_or_field": "DocField",
                "field_name": fieldname,
                "property": "hidden",
                "value": "1",
                "property_type": "Check"
            })
            ps.insert(ignore_permissions=True)
        
        # 2. Position Telephony Trunk ID after Session ID
        frappe.db.delete("Custom Field", {"dt": dt, "fieldname": "telephony_trunk_id"})
        cf = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": dt,
            "fieldname": "telephony_trunk_id",
            "label": "Telephony Trunk ID",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "session_id",
            "in_standard_filter": 1
        })
        cf.insert(ignore_permissions=True)

        # 3. Handle Telephony Account field
        frappe.db.delete("Custom Field", {"dt": "Voice AI Telephony Account", "fieldname": "telephony_trunk_id"})
        cf_acc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Voice AI Telephony Account",
            "fieldname": "telephony_trunk_id",
            "label": "Telephony Trunk ID (Vobiz)",
            "fieldtype": "Data",
            "read_only": 0,
            "insert_after": "account_name"
        })
        cf_acc.insert(ignore_permissions=True)

        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: UI Cleaned and Repositioned.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    cleanup_ui()
