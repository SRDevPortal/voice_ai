import frappe
from voice_ai.voice_ai.processor import create_encounter_queue

def fresh_natural_test():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        phone = "9873362268"
        
        # 1. Reset all old records
        frappe.db.set_value("Voice AI Encounter Queue", {
            "customer_phone": ["like", f"%{phone}"],
            "queue_status": ["!=", "Completed"]
        }, "queue_status", "Completed", update_modified=False)
        frappe.db.commit()
        print(f"Cleared old records for {phone}")

        # 2. Create and initiate
        payload = {
            "patient_name": "Triple-Lock Verification",
            "phone_number": "9873362268",
            "notes": "Testing raw input logging"
        }
        
        print("Launching Fresh Call...")
        result = create_encounter_queue(
            customer_phone="9873362268",
            call_queue="CQ-00003",
            submit_now=1,
            payload_json=payload
        )
        
        frappe.db.commit()
        print(f"SUCCESS: Created {result['queue_name']}")
        
        # Verify trunk ID is stamped
        trunk_id = frappe.db.get_value("Voice AI Encounter Queue", result["queue_name"], "telephony_trunk_id")
        print(f"Stamped Trunk ID: {trunk_id}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    fresh_natural_test()
