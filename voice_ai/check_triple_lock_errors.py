import frappe

def check_recent_errors():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        errors = frappe.get_all("Error Log", 
            filters={"message": ["like", "%Encounter Queue%not found%"]},
            order_by="creation desc",
            limit=5,
            fields=["creation", "message", "text_content"]
        )
        for err in errors:
            print(f"Time: {err.creation}")
            print(f"Message: {err.message}")
            print("-" * 50)
            
        # Also check the latest Encounter Queue record to see what's actually there
        latest = frappe.get_all("Voice AI Encounter Queue", 
            order_by="creation desc", 
            limit=1, 
            fields=["name", "customer_phone", "telephony_trunk_id", "queue_status"]
        )
        print(f"Latest Record in DB: {latest}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_recent_errors()
