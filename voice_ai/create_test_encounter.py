import frappe
from voice_ai.voice_ai.processor import create_encounter_queue

def create_test_record():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # We use the sample data from your previous webhook
        payload = {
            "patient_name": "Vishal Test",
            "patient_encounter": "HLC-ENC-2026-567230",
            "phone_number": "9873362268",
            "amount": "900",
            "address": "AAA, Ghaziabad, Uttar Pradesh - 202121, India"
        }
        
        result = create_encounter_queue(
            customer_phone="9873362268",
            call_queue="CQ-00003",
            submit_now=0, # DO NOT CALL YET
            payload_json=payload
        )
        
        frappe.db.commit()
        print(f"SUCCESS: Created Encounter Queue Record: {result.get('queue_name')}")
        print(f"Assigned Account: {result.get('assigned_account')}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    create_test_record()
