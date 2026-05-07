import frappe

def check_duplicate_records():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        from voice_ai.voice_ai.processor import normalize_phone_number
        phone = "7007186368"
        norm_phone = normalize_phone_number(phone)
        
        print(f"=== SEARCHING ALL RECORDS FOR PHONE: {phone} (Norm: {norm_phone}) ===")
        records = frappe.get_all("Voice AI Encounter Queue", 
            filters={"customer_phone": ["like", f"%{norm_phone}"]},
            fields=["name", "queue_status", "telephony_trunk_id", "modified", "creation"],
            order_by="creation desc"
        )
        
        for r in records:
            print(f"ID: {r.name} | Status: {r.queue_status} | Trunk: {r.telephony_trunk_id} | Created: {r.creation} | Modified: {r.modified}")
            
        if not records:
            print("No records found for this phone number.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_duplicate_records()
