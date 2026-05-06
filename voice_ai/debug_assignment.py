import frappe
from voice_ai.voice_ai.assignment import assign_worker_to_queue_doc, ACTIVE_ASSIGNMENT_STATUSES

def debug_assignment_failure():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        account_name = "Test Vobiz Line"
        
        # 1. Check current load
        load_count = frappe.db.count("Voice AI Encounter Queue", {
            "assigned_account": account_name,
            "queue_status": ["in", list(ACTIVE_ASSIGNMENT_STATUSES)]
        })
        print(f"Current Load for {account_name}: {load_count}")
        
        # 2. If load is high, clear it for testing
        if load_count > 0:
            frappe.db.set_value("Voice AI Encounter Queue", {
                "assigned_account": account_name,
                "queue_status": ["in", list(ACTIVE_ASSIGNMENT_STATUSES)]
            }, "queue_status", "Completed", update_modified=False)
            frappe.db.commit()
            print(f"Cleared {load_count} records to reset capacity.")

        # 3. Now try to assign the test record kmo9ks9anf
        doc = frappe.get_doc("Voice AI Encounter Queue", "kmo9ks9anf")
        doc.queue_status = "Pending"
        account = assign_worker_to_queue_doc(doc)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"Assigned Account: {account}")
        print(f"Trunk ID on Record: {doc.telephony_trunk_id}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    debug_assignment_failure()
