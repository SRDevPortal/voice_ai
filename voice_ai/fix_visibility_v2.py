import frappe

def fix_visibility_v2():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Update Telephony Account field to be visible and editable
        frappe.db.set_value("Custom Field", {"dt": "Voice AI Telephony Account", "fieldname": "telephony_trunk_id"}, {
            "read_only": 0,
            "hidden": 0,
            "label": "TELEPHONY TRUNK ID (PASTE HERE)",
            "insert_after": "account_name"
        })
        
        # Update Encounter Queue field to be visible (even if empty)
        frappe.db.set_value("Custom Field", {"dt": "Voice AI Encounter Queue", "fieldname": "telephony_trunk_id"}, {
            "read_only": 0,
            "hidden": 0,
            "insert_after": "call_queue"
        })
        
        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: Updated fields to be editable and visible.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    fix_visibility_v2()
