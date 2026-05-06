import frappe

def cleanup_ui():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        dt = "Voice AI Encounter Queue"
        
        # 1. Hide unwanted fields
        fields_to_hide = ["order_id", "customer_name", "external_queue_id"]
        for fieldname in fields_to_hide:
            frappe.make_property_setter(
                doctype=dt,
                fieldname=fieldname,
                property="hidden",
                value=1,
                property_type="Check"
            )
        
        # 2. Position Telephony Trunk ID after Session ID (Right Column)
        # Session ID is often a custom field or standard. Let's find where it is.
        frappe.db.set_value("Custom Field", {"dt": dt, "fieldname": "telephony_trunk_id"}, {
            "insert_after": "session_id",
            "label": "Telephony Trunk ID",
            "read_only": 1
        })

        # 3. Ensure editable in Account
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
