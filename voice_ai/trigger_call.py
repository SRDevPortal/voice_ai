import frappe
from voice_ai.voice_ai.processor import submit_to_elevenlabs

def trigger_call():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        name = "44c3p9p6l8"
        doc = frappe.get_doc("Voice AI Encounter Queue", name)
        
        print(f"Triggering ElevenLabs call for {doc.name}...")
        result = submit_to_elevenlabs(doc)
        
        frappe.db.commit()
        print(f"ElevenLabs Response: {result}")
        print(f"New Status: {doc.queue_status}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    trigger_call()
