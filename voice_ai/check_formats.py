import frappe

def check_field_formats():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Check the record we created
        name = "kmo9ks9anf"
        record = frappe.db.get_value("Voice AI Encounter Queue", name, ["customer_phone", "telephony_trunk_id", "queue_status"], as_dict=True)
        print(f"Record {name} in DB:")
        print(f"  Phone: '{record.customer_phone}'")
        print(f"  Trunk ID: '{record.telephony_trunk_id}'")
        print(f"  Status: {record.queue_status}")
        
        # Check the Telephony Account as well
        acc = frappe.get_all("Voice AI Telephony Account", fields=["name", "telephony_trunk_id"])
        print(f"Telephony Accounts in DB: {acc}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_field_formats()
