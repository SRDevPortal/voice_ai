import frappe
from voice_ai.voice_ai.assignment import assign_worker_to_queue_doc

def force_assign_specific():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        name = "kmo9ks9anf"
        doc = frappe.get_doc("Voice AI Encounter Queue", name)
        print(f"Current Status: {doc.queue_status}")
        
        # Reset status if needed
        if doc.queue_status != "Pending":
            doc.queue_status = "Pending"
            
        account = assign_worker_to_queue_doc(doc)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"Assigned Account: {account}")
        print(f"Trunk ID on Record: {doc.telephony_trunk_id}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    force_assign_specific()
