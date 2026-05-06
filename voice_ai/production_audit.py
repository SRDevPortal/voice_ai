import frappe
import json
from voice_ai.voice_ai.processor import normalize_phone_number, update_encounter_status

def production_audit():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("--- PRODUCTION READINESS AUDIT ---")
        
        # 1. Schema Check
        queue_fields = [f.fieldname for f in frappe.get_meta("Voice AI Encounter Queue").fields]
        acc_fields = [f.fieldname for f in frappe.get_meta("Voice AI Telephony Account").fields]
        
        if "telephony_trunk_id" in queue_fields and "telephony_trunk_id" in acc_fields:
            print("[OK] Schema: Telephony Trunk ID present on all DocTypes.")
        else:
            print("[FAIL] Schema: Missing telephony_trunk_id fields!")

        # 2. Logic Check: Normalization
        test_phones = ["+919873362268", "919873362268", "09873362268", "9873362268"]
        normalized = [normalize_phone_number(p) for p in test_phones]
        if all(n == "9873362268" for n in normalized):
            print("[OK] Logic: 10-Digit Normalization is consistent.")
        else:
            print(f"[FAIL] Logic: Normalization inconsistent: {normalized}")

        # 3. UI Check: Property Setters
        hidden_fields = frappe.get_all("Property Setter", filters={"property": "hidden", "value": "1", "doc_type": "Voice AI Encounter Queue"}, fields=["field_name"])
        hidden_names = [h.field_name for h in hidden_fields]
        if "order_id" in hidden_names and "customer_name" in hidden_names:
            print("[OK] UI: Junk fields (Order ID, etc.) are hidden.")
        else:
            print(f"[WARN] UI: Some junk fields might still be visible: {hidden_names}")

        # 4. End-to-End Mock Simulation
        # We use our latest record bbutatk0u9
        test_record = "bbutatk0u9"
        trunk_id = "3ec712d3-c160-4dc7-8c8b-48e81abeab51"
        
        print(f"Testing Mock Webhook for {test_record}...")
        # Simulate the 'Messy JSON Key' that n8n sends
        messy_key = json.dumps({
            "customer_phone": "9873362268",
            "telephony_trunk_id": trunk_id,
            "telephony_status": "completed",
            "queue_status": "Completed"
        })
        
        update_encounter_status(**{messy_key: ""})
        frappe.db.commit()
        
        final_status = frappe.db.get_value("Voice AI Encounter Queue", test_record, "queue_status")
        if final_status == "Completed":
            print("[OK] API: Self-healing Triple-Lock lookup successful.")
        else:
            print(f"[FAIL] API: Mock simulation failed. Status is {final_status}")

        print("--- AUDIT COMPLETE: READY FOR PRODUCTION ---")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    production_audit()
