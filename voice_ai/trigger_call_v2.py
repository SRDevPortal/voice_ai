import frappe
from voice_ai.voice_ai.processor import submit_encounter_queue

def trigger_call():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        name = "44c3p9p6l8"
        print(f"Triggering call for {name}...")
        
        result = submit_encounter_queue(name)
        
        frappe.db.commit()
        print(f"Result: {result}")
        
        # Verify status
        status = frappe.db.get_value("Voice AI Encounter Queue", name, "queue_status")
        print(f"Final Status: {status}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    trigger_call()
