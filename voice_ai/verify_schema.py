import frappe

def verify():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    try:
        call_queues = frappe.get_all("Call Queue", limit=1)
        queue_name = call_queues[0].name if call_queues else None
        
        doc = frappe.get_doc({
            "doctype": "Voice AI Encounter Queue",
            "call_queue": queue_name,
            "patient_encounter": "REMOTE-ENC-123",
            "patient": "HLC-PAT-2025-19052",  # Should save fine now as string
            "customer": "HLC-CUST-2025-9999", # Should save fine now as string
            "telephony_status": "queued"
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"✅ Success! Created queue {doc.name} with external patient ID: {doc.patient} and external customer ID: {doc.customer}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    verify()
