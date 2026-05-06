import frappe
from voice_ai.voice_ai.processor import create_encounter_queue

def test_full_flow():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    try:
        # 1. Setup Telephony Account
        account_name = "Test Vobiz Line"
        if not frappe.db.exists("Voice AI Telephony Account", account_name):
            acc = frappe.get_doc({
                "doctype": "Voice AI Telephony Account",
                "account_name": account_name,
                "enabled": 1,
                "status": "ready",
                "telephony_provider": "vobiz",
                "default_phone_number_id": "VOBIZ-PHONE-001",
                "max_concurrent_calls": 5
            })
            acc.insert(ignore_permissions=True)
            acc_id = acc.name
            print(f"Created Telephony Account: {acc_id}")
        else:
            acc_id = account_name
            print(f"Using existing Telephony Account: {acc_id}")

        # 2. Setup Call Queue
        # Search by queue_name since name is a naming series
        existing_cq = frappe.db.get_value("Call Queue", {"queue_name": "Test AI Queue"}, "name")
        if not existing_cq:
            cq = frappe.get_doc({
                "doctype": "Call Queue",
                "queue_name": "Test AI Queue",
                "enabled": 1,
                "status": "Open",
                "provider": "elevenlabs",
                "telephony_account": acc_id,
                "default_agent_id": "AGENT-ABC-123"
            })
            cq.insert(ignore_permissions=True)
            cq_id = cq.name
            print(f"Created Call Queue: {cq_id}")
        else:
            cq_id = existing_cq
            cq = frappe.get_doc("Call Queue", cq_id)
            cq.telephony_account = acc_id
            cq.default_agent_id = "AGENT-ABC-123"
            cq.save(ignore_permissions=True)
            print(f"Using existing Call Queue: {cq_id}")

        frappe.db.commit()

        # 3. Simulate n8n API Call (Zero Friction)
        # We pass the cq_id (naming series ID)
        test_phone = "9873362268"
        payload = {
            "customer_name": "Vishal",
            "reason": "Appointment Reminder",
            "amount_due": 500
        }

        print(f"Simulating API call for {test_phone} using queue {cq_id}...")
        result = create_encounter_queue(
            customer_phone=test_phone,
            payload_json=payload,
            submit_now=1,
            call_queue=cq_id
        )

        queue_id = result.get("name")
        print(f"Result: {result}")

        # 4. Verify the record
        doc = frappe.get_doc("Voice AI Encounter Queue", queue_id)
        print(f"Record {doc.name} status: {doc.queue_status}")
        print(f"Assigned Account: {doc.assigned_account}")
        print(f"Assigned Agent: {doc.assigned_agent}")

        if doc.assigned_account == acc_id and doc.assigned_agent == "AGENT-ABC-123":
            print("SUCCESS: Inheritance and Assignment working perfectly!")
        else:
            print(f"FAILURE: Inheritance or Assignment failed. Account: {doc.assigned_account}, Agent: {doc.assigned_agent}")

    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_full_flow()
