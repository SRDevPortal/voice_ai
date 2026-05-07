import frappe
import time
from voice_ai.voice_ai.processor import create_encounter_queue, normalize_phone_number
from voice_ai.voice_ai.assignment import assign_worker_to_queue_doc

def simulation_15_cases():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("=== STARTING 15-ENCOUNTER EDGE CASE SIMULATION ===")
        # 1. Setup Test Data
        acc_name = "Test Vobiz Line"
        call_queue = "CQ-00003"
        
        # Ensure account has capacity 5
        frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 5)
        # Ensure account is enabled
        frappe.db.set_value("Voice AI Telephony Account", acc_name, "enabled", 1)
        frappe.db.commit()
        
        test_phones = [f"90000000{i:02d}" for i in range(1, 16)]
        
        results = []
        
        # Scenario Group 1: 5 Normal records (different phones)
        print("\nGroup 1: 5 Normal Records...")
        for i in range(5):
            rec = create_encounter_queue(customer_phone=test_phones[i], call_queue=call_queue)
            results.append(rec)
            
        # Scenario Group 2: 2 Busy records (same phone as Record 1)
        print("Group 2: 2 Busy Records...")
        for i in range(2):
            rec = create_encounter_queue(customer_phone=test_phones[0], call_queue=call_queue)
            results.append(rec)
            
        # Scenario Group 3: 3 Mismatched Queue names
        print("Group 3: 3 Mismatched Queues...")
        for i in range(3):
            rec = create_encounter_queue(customer_phone=test_phones[i+7], call_queue="NON_EXISTENT_QUEUE")
            results.append(rec)
            
        # Scenario Group 4: 1 Skeleton Account (No Trunk ID)
        print("Group 4: 1 Skeleton Account...")
        # Create a temp skeleton account
        skeleton = "Skeleton Account"
        if not frappe.db.exists("Voice AI Telephony Account", skeleton):
            doc = frappe.new_doc("Voice AI Telephony Account")
            doc.telephony_account_name = skeleton
            doc.telephony_trunk_id = "" # EMPTY TRUNK ID
            doc.max_concurrent_calls = 5
            doc.enabled = 1
            doc.status = "idle"
            doc.insert()
        
        # Link it to a temp queue
        sk_queue = "CQ-SKELETON"
        if not frappe.db.exists("Call Queue", sk_queue):
            qdoc = frappe.new_doc("Call Queue")
            qdoc.queue_name = sk_queue
            qdoc.telephony_account = skeleton
            qdoc.enabled = 1
            qdoc.status = "Open"
            qdoc.insert()
            
        rec_sk = create_encounter_queue(customer_phone=test_phones[10], call_queue=sk_queue)
        results.append(rec_sk)
        
        # Scenario Group 5: 4 Capacity-blocked records
        # (Since we have 5 normal calls and 1 skeleton call, we are at 6 load. 
        # But we need to assign them to see the block).
        print("Group 5: 4 Capacity Blocks...")
        for i in range(4):
            rec = create_encounter_queue(customer_phone=test_phones[i+11], call_queue=call_queue)
            results.append(rec)

        # Final Audit
        print("\n=== FINAL AUDIT REPORT ===")
        print(f"{'#':<3} | {'Phone':<12} | {'Account':<20} | {'Trunk ID':<40} | {'Status'}")
        print("-" * 100)
        
        for idx, res in enumerate(results):
            name = res["queue_name"]
            doc = frappe.get_doc("Voice AI Encounter Queue", name)
            acc = doc.assigned_account or "NONE"
            trunk = doc.telephony_trunk_id or "MISSING"
            print(f"{idx+1:<3} | {doc.customer_phone:<12} | {acc:<20} | {trunk:<40} | {doc.queue_status}")

    finally:
        frappe.destroy()

if __name__ == "__main__":
    simulation_15_cases()
