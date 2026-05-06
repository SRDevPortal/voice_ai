import frappe
from voice_ai.voice_ai.processor import create_encounter_queue

def natural_flow_test():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # We follow the natural flow with submit_now=1
        payload = {
            "patient_name": "Natural Flow Test",
            "phone_number": "9873362268",
            "notes": "Testing the full triple-lock cycle"
        }
        
        print("Starting Natural Flow (Creation -> Assignment -> ElevenLabs)...")
        result = create_encounter_queue(
            customer_phone="9873362268",
            call_queue="CQ-00003",
            submit_now=1, # FULL FLOW
            payload_json=payload
        )
        
        frappe.db.commit()
        print(f"SUCCESS: Result: {result}")
        
        # Check current status
        status = frappe.db.get_value("Voice AI Encounter Queue", result["queue_name"], "queue_status")
        print(f"Record Status: {status}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    natural_flow_test()
