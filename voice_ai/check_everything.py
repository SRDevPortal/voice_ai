import frappe

def check_everything():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("=== ALL CALL QUEUES ===")
        queues = frappe.get_all("Call Queue", fields=["name", "queue_name", "enabled", "status", "telephony_account"])
        for q in queues:
            print(f"Name: {q.name} | Display Name: {q.queue_name} | Enabled: {q.enabled} | Status: {q.status} | Account: {q.telephony_account}")
            
        print("\n=== PENDING ENCOUNTER QUEUE RECORDS ===")
        pending = frappe.get_all("Voice AI Encounter Queue", 
            filters={"queue_status": ["in", ["Pending", "Assigned"]]},
            fields=["name", "customer_phone", "call_queue", "assigned_account", "telephony_trunk_id", "creation"]
        )
        for p in pending:
            print(f"Name: {p.name} | Phone: {p.customer_phone} | Queue: {p.call_queue} | Account: {p.assigned_account} | Trunk: {p.telephony_trunk_id} | Created: {p.creation}")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_everything()
