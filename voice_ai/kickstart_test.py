import frappe
from voice_ai.voice_ai.processor import submit_encounter_queue

def kickstart_test():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        phone = "9873362268"
        name = "7t6c06i1i0"
        
        # 1. Clear old records for this phone
        frappe.db.set_value("Voice AI Encounter Queue", {
            "customer_phone": ["like", f"%{phone}"],
            "name": ["!=", name],
            "queue_status": ["!=", "Completed"]
        }, "queue_status", "Completed", update_modified=False)
        frappe.db.commit()
        print(f"Cleared old records for {phone}")

        # 2. Kickstart the new record
        print(f"Submitting {name}...")
        result = submit_encounter_queue(name)
        frappe.db.commit()
        
        doc = frappe.get_doc("Voice AI Encounter Queue", name)
        print(f"Final Status: {doc.queue_status}")
        print(f"Assigned Account: {doc.assigned_account}")
        print(f"Trunk ID: {doc.telephony_trunk_id}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    kickstart_test()
