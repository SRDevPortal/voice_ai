import frappe
from voice_ai.voice_ai.processor import submit_encounter_queue, create_encounter_queue, update_encounter_status

def stress_test():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("--- STARTING SCENARIO STRESS TEST ---")
        phone = "9988776655"
        
        # Scenario 1: Global Busy Filter (Double-Call Protection)
        print("\n1. Testing Double-Call Protection...")
        # Create Record 1
        rec1 = create_encounter_queue(customer_phone=phone, call_queue="CQ-00003")
        name1 = rec1["queue_name"]
        # Manually mark as In Progress to simulate a live call
        frappe.db.set_value("Voice AI Encounter Queue", name1, "queue_status", "In Progress")
        frappe.db.commit()
        
        # Create Record 2 for the same phone
        rec2 = create_encounter_queue(customer_phone=phone, call_queue="CQ-00003")
        name2 = rec2["queue_name"]
        
        # Try to submit Record 2
        res2 = submit_encounter_queue(name2)
        status2 = frappe.db.get_value("Voice AI Encounter Queue", name2, "queue_status")
        
        if status2 == "Pending":
            print(f"[SUCCESS] Record 2 stayed Pending because Phone {phone} is Busy.")
        else:
            print(f"[FAIL] Record 2 was picked up! Status: {status2}")

        # Scenario 2: Account Capacity (Line Full)
        print("\n2. Testing Capacity Limit...")
        acc_name = "Test Vobiz Line"
        # Set max concurrency to 0 temporarily
        old_max = frappe.db.get_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls")
        frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 0)
        frappe.db.commit()
        
        new_phone = "1122334455"
        rec3 = create_encounter_queue(customer_phone=new_phone, call_queue="CQ-00003")
        res3 = submit_encounter_queue(rec3["queue_name"])
        
        status3 = frappe.db.get_value("Voice AI Encounter Queue", rec3["queue_name"], "queue_status")
        if status3 == "Pending":
            print("[SUCCESS] Record stayed Pending because the Account was Full.")
        else:
            print(f"[FAIL] Record was picked up! Status: {status3}")
            
        # Restore account
        frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", old_max)
        frappe.db.commit()

        print("\n--- STRESS TEST COMPLETE ---")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    stress_test()
