import frappe

def full_audit():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        phone_last_10 = "9873362268"
        
        # 1. Audit ALL records for this phone
        records = frappe.get_all("Voice AI Encounter Queue", 
            filters={"customer_phone": ["like", f"%{phone_last_10}"]},
            fields=["name", "queue_status", "assigned_account", "customer_phone"]
        )
        print(f"All Records for {phone_last_10}: {records}")

        # 2. Audit Telephony Account status
        acc = frappe.get_all("Voice AI Telephony Account", 
            fields=["name", "enabled", "status", "max_concurrent_calls"]
        )
        print(f"Account Status: {acc}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    full_audit()
