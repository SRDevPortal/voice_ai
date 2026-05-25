import frappe
import json
from voice_ai.voice_ai.processor import submit_encounter_queue

def run():
    encounter_name = "4u7mfu446v"
    
    # 1. Update Telephony Account Master Test Line with the newly created Outbound Trunk ID
    telephony_account_name = "Master Test Line"
    telephony_account = frappe.get_doc("Voice AI Telephony Account", telephony_account_name)
    telephony_account.telephony_trunk_id = "ST_nUucndSqJFQq"
    telephony_account.save(ignore_permissions=True)
    print(f"Updated Telephony Account {telephony_account_name} trunk ID to ST_nUucndSqJFQq.")
    
    # Reset encounter status to Pending so it can be processed again
    print(f"Resetting Encounter Queue record {encounter_name} to Pending and trunk ID to ST_nUucndSqJFQq...")
    encounter = frappe.get_doc("Voice AI Encounter Queue", encounter_name)
    encounter.queue_status = "Pending"
    encounter.telephony_status = "queued"
    encounter.telephony_trunk_id = "ST_nUucndSqJFQq"
    encounter.assigned_account = "Master Test Line"
    encounter.save(ignore_permissions=True)
    frappe.db.commit()
    
    # Trigger the call using submit_encounter_queue
    print("Triggering the LiveKit outbound call using ST_nUucndSqJFQq...")
    try:
        # We run it synchronously
        result = submit_encounter_queue(encounter.name, timeout=30)
        print("API CALL RESULT:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"API CALL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        
    # Fetch updated record status
    frappe.db.rollback() # Clear local cache
    updated_encounter = frappe.get_doc("Voice AI Encounter Queue", encounter.name)
    print("\nUPDATED ENCOUNTER RECORD IN DB:")
    print(f"Queue Status: {updated_encounter.queue_status}")
    print(f"Telephony Status: {updated_encounter.telephony_status}")
    print(f"Job ID: {updated_encounter.job_id}")
    print(f"Session ID (Room): {updated_encounter.session_id}")
    print(f"Notes: {updated_encounter.notes}")

if __name__ == "__main__":
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        run()
    finally:
        frappe.destroy()
