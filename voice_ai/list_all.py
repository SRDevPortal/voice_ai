import frappe

def list_recent():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        results = frappe.get_all("Voice AI Encounter Queue", 
            fields=["name", "customer_phone", "queue_status", "creation"],
            order_by="creation desc",
            limit=10
        )
        for r in results:
            print(f"ID: {r.name} | Phone: {r.customer_phone} | Status: {r.queue_status} | Created: {r.creation}")
            
        if not results:
            print("The Encounter Queue table is EMPTY!")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    list_recent()
