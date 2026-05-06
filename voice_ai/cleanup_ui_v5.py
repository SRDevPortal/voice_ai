import frappe

def cleanup_ui():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # 1. Encounter Queue Layout
        dt = "Voice AI Encounter Queue"
        
        # Hide fields
        for field in ["order_id", "customer_name", "external_queue_id"]:
            frappe.db.delete("Property Setter", {"doc_type": dt, "field_name": field, "property": "hidden"})
            ps = frappe.get_doc({
                "doctype": "Property Setter",
                "doc_type": dt,
                "field_name": field,
                "property": "hidden",
                "value": "1",
                "property_type": "Check",
                "doctype_or_field": "DocField"
            })
            ps.insert(ignore_permissions=True)
            
        # Reposition Trunk ID
        frappe.db.delete("Property Setter", {"doc_type": dt, "field_name": "telephony_trunk_id", "property": "insert_after"})
        ps_move = frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": dt,
            "field_name": "telephony_trunk_id",
            "property": "insert_after",
            "value": "session_id",
            "property_type": "Data",
            "doctype_or_field": "DocField"
        })
        ps_move.insert(ignore_permissions=True)

        # 2. Telephony Account Layout
        dt_acc = "Voice AI Telephony Account"
        frappe.db.delete("Property Setter", {"doc_type": dt_acc, "field_name": "telephony_trunk_id", "property": "insert_after"})
        ps_move_acc = frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": dt_acc,
            "field_name": "telephony_trunk_id",
            "property": "insert_after",
            "value": "account_name",
            "property_type": "Data",
            "doctype_or_field": "DocField"
        })
        ps_move_acc.insert(ignore_permissions=True)

        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: UI Cleaned up via Property Setters.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    cleanup_ui()
