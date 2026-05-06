import frappe
from voice_ai.voice_ai.assignment import assign_worker_to_queue_doc

def clean_and_assign():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        phone = "9873362268"
        
        # 1. Mark old records as Completed
        old_records = frappe.get_all("Voice AI Encounter Queue", 
            filters={
                "customer_phone": phone,
                "queue_status": ["in", ["Assigned", "Picked", "In Progress"]]
            }
        )
        for row in old_records:
            frappe.db.set_value("Voice AI Encounter Queue", row.name, "queue_status", "Completed")
        
        frappe.db.commit()
        print(f"Cleaned up {len(old_records)} old records for {phone}")

        # 2. Assign the latest record
        latest = frappe.get_all("Voice AI Encounter Queue",
            filters={"customer_phone": phone, "queue_status": "Pending"},
            order_by="creation desc",
            limit=1
        )
        
        if latest:
            doc = frappe.get_doc("Voice AI Encounter Queue", latest[0].name)
            account = assign_worker_to_queue_doc(doc)
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"SUCCESS: Assigned {doc.name} to {account}")
            print(f"Trunk ID on Record: {doc.telephony_trunk_id}")
        else:
            print("No pending records found to assign.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    clean_and_assign()
