import frappe

def deep_scan():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Search for any record containing the last 5 digits of the phone
        partial = "86368"
        print(f"=== DEEP SCAN FOR PARTIAL PHONE: {partial} ===")
        records = frappe.get_all("Voice AI Encounter Queue", 
            filters={"customer_phone": ["like", f"%{partial}%"]},
            fields=["name", "customer_phone", "queue_status", "telephony_trunk_id", "modified"],
            order_by="creation desc"
        )
        
        for r in records:
            print(f"ID: {r.name} | Phone: {r.customer_phone} | Status: {r.queue_status} | Trunk: {r.telephony_trunk_id} | Modified: {r.modified}")
            
        if not records:
            print("Still nothing found. This is extremely unusual.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    deep_scan()
