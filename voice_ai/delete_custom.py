import frappe

def delete_redundant_custom_fields():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Delete custom fields with the same name as standard fields
        frappe.db.delete("Custom Field", {"fieldname": "telephony_trunk_id"})
        frappe.db.commit()
        frappe.clear_cache()
        print("SUCCESS: Deleted redundant custom fields.")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    delete_redundant_custom_fields()
