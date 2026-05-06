import frappe
import json

def run_test():
    print("Initializing Frappe for test...")
    frappe.init(site="mysite.localhost")
    frappe.connect()

    try:
        call_queues = frappe.get_all("Call Queue", limit=1)
        queue_name = call_queues[0].name if call_queues else None
        
        print(f"Using Call Queue: {queue_name}")

        dynamic_params = {
            "patient_name": "John Doe Test",
            "outstanding_amount": 1500.0,
            "next_appointment": "2026-05-10"
        }

        print("Creating Voice AI Encounter Queue record...")
        queue_doc = frappe.get_doc({
            "doctype": "Voice AI Encounter Queue",
            "call_queue": queue_name,
            "patient_encounter": "TEST-ENC-001",
            "customer_phone": "9873362268",
            "payload_json": json.dumps(dynamic_params),
            "telephony_status": "queued"
        })
        queue_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        print(f"✅ Successfully created Voice AI Encounter Queue: {queue_doc.name}")
        print(f"Customer Phone: {queue_doc.customer_phone}")
        print(f"Payload JSON: {queue_doc.payload_json}")

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    run_test()
