import frappe

def cleanup_ui():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        dt = "Voice AI Encounter Queue"
        
        # 1. Hide unwanted fields
        fields_to_hide = ["order_id", "customer_name", "external_queue_id"]
        for fieldname in fields_to_hide:
            # Check if it's a standard field or custom field
            is_custom = frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname})
            if is_custom:
                frappe.db.set_value("Custom Field", {"dt": dt, "fieldname": fieldname}, "hidden", 1)
            else:
                # Use Property Setter for standard fields
                frappe.make_property_setter(dt, fieldname, "hidden", 1, "Check")
        
        # 2. Position Telephony Trunk ID after Session ID (Right Column)
        frappe.db.set_value("Custom Field", {"dt": dt, "fieldname": "telephony_trunk_id"}, {
            "insert_after": "session_id",
            "label": "Telephony Trunk ID",
            "read_only": 1 # Back to read-only since it's just for display here
        })

        # 3. Also ensure Telephony Trunk ID is editable in the Account DocType (where the user needs to paste it)
        frappe.db.set_value("Custom Field", {"dt": "Voice AI Telephony Account", "fieldname": "telephony_trunk_id"}, {
            "read_only": 0,
            "label": "Telephony Trunk ID (Vobiz)",
            "insert_after": "account_name"
        })

        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: Cleaned up UI and repositioned Trunk ID.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    cleanup_ui()
