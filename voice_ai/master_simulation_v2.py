import frappe
import json
import time
from voice_ai.voice_ai.processor import submit_encounter_queue, create_encounter_queue, update_encounter_status, normalize_phone_number
from voice_ai.voice_ai.assignment import get_account_active_load

def master_simulation():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("=== MASTER PRODUCTION SIMULATION START ===")
        results = []
        acc_name = "Test Vobiz Line"
        call_queue = "CQ-00003"
        
        # Use a unique phone for each run to avoid Busy Filter collisions
        ts = str(int(time.time()))[-10:]
        phone = ts
        
        # Scenario 1 & 7: Normal Initiation + Amnesia Check
        print(f"\n[Sim 1] Normal Initiation & Persistence (Phone: {phone})...")
        rec1 = create_encounter_queue(customer_phone=phone, call_queue=call_queue)
        name1 = rec1["queue_name"]
        res1 = submit_encounter_queue(name1)
        
        doc1 = frappe.get_doc("Voice AI Encounter Queue", name1)
        if doc1.queue_status == "In Progress" and doc1.telephony_trunk_id:
            results.append("1. Normal Flow + Persistence: [PASS]")
        else:
            results.append(f"1. Normal Flow + Persistence: [FAIL] Status={doc1.queue_status}, Trunk={doc1.telephony_trunk_id}")

        # Scenario 2 & 6: Triple-Lock + Self-Healing Webhook
        print("[Sim 2] Triple-Lock + Self-Healing...")
        messy_key = json.dumps({
            "customer_phone": phone,
            "telephony_trunk_id": doc1.telephony_trunk_id,
            "queue_status": "Completed"
        })
        update_encounter_status(**{messy_key: ""})
        frappe.db.commit()
        
        status2 = frappe.db.get_value("Voice AI Encounter Queue", name1, "queue_status")
        if status2 == "Completed":
            results.append("2. Triple-Lock + Self-Healing: [PASS]")
        else:
            results.append(f"2. Triple-Lock + Self-Healing: [FAIL] Status={status2}")

        # Scenario 3: Fuzzy Phone Matching
        print("[Sim 3] Fuzzy Phone Matching...")
        # Manually set it back to active status for busy check
        frappe.db.set_value("Voice AI Encounter Queue", name1, "queue_status", "In Progress")
        frappe.db.commit()
        
        phone_v2 = "+91" + phone
        from voice_ai.voice_ai.assignment import is_phone_busy_globally
        is_busy = is_phone_busy_globally(phone_v2)
        if is_busy:
            results.append("3. Fuzzy Phone Matching (Busy Check): [PASS]")
        else:
            results.append("3. Fuzzy Phone Matching (Busy Check): [FAIL]")
        
        # Scenario 4 & 5: Capacity
        print("[Sim 4/5] Capacity Limit...")
        # Finish the previous one
        frappe.db.set_value("Voice AI Encounter Queue", name1, "queue_status", "Completed")
        
        # Set capacity to 0
        frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 0)
        frappe.db.commit()
        
        # Create a fresh record with a fresh phone
        phone_cap = "1" + ts[1:]
        rec5 = create_encounter_queue(customer_phone=phone_cap, call_queue=call_queue)
        res5 = submit_encounter_queue(rec5["queue_name"])
        
        status5 = frappe.db.get_value("Voice AI Encounter Queue", rec5["queue_name"], "queue_status")
        if status5 == "Pending":
            results.append("4/5. Capacity Limit: [PASS]")
        else:
            results.append(f"4/5. Capacity Limit: [FAIL] Status={status5}")
            
        # Restore capacity
        frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 5)
        frappe.db.commit()

        # Final Report
        print("\n=== FINAL SIMULATION REPORT ===")
        for r in results:
            print(r)
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    master_simulation()
