import frappe
from voice_ai.voice_ai.processor import create_encounter_queue

def fresh_test_setup():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # 1. Mark all old records as Completed
        old_count = frappe.db.count("Voice AI Encounter Queue", {"queue_status": ["!=", "Completed"]})
        frappe.db.set_value("Voice AI Encounter Queue", {"queue_status": ["!=", "Completed"]}, "queue_status", "Completed", update_modified=False)
        frappe.db.commit()
        print(f"CLEARED: Marked {old_count} old records as Completed.")

        # 2. Create fresh record for 9873362268
        payload = {
            "patient_name": "Fresh Test",
            "phone_number": "9873362268",
            "notes": "Testing last-10 digit match"
        }
        
        result = create_encounter_queue(
            customer_phone="9873362268",
            call_queue="CQ-00003",
            submit_now=0, # Manual test
            payload_json=payload
        )
        
        # Force it into 'Assigned' status so Vobiz can find it
        # (Assignment usually happens automatically, but we force it here to be safe)
        from voice_ai.voice_ai.assignment import assign_worker_to_queue_doc
        doc = frappe.get_doc("Voice AI Encounter Queue", result["queue_name"])
        assign_worker_to_queue_doc(doc)
        doc.save(ignore_permissions=True)
        
        frappe.db.commit()
        print(f"SUCCESS: Created Fresh Record: {doc.name}")
        print(f"Assigned Account: {doc.assigned_account}")
        print(f"Trunk ID: {doc.telephony_trunk_id}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    fresh_test_setup()
