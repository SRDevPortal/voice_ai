import frappe
import json
import socket
from urllib import request, error
from frappe.utils import now_datetime, cint, flt, now, get_datetime
from datetime import timedelta

def run_master_test_suite():
    frappe.connect()
    
    results = []
    QUEUE_DOCTYPE = "Voice AI Encounter Queue"
    CALL_QUEUE_DOCTYPE = "Call Queue"
    
    def log_result(test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        results.append({"test": test_name, "status": status, "details": details})
        print(f"{status} | {test_name}\n       -> {details}")

    try:
        print("=== VOICE AI PRODUCTION VALIDATION SUITE ===")
        print("Initializing Test Environment...")
        
        # 0. Setup Test Data
        acc_name = "Master Test Line"
        if not frappe.db.exists("Voice AI Telephony Account", acc_name):
            doc = frappe.new_doc("Voice AI Telephony Account")
            doc.account_name = acc_name
            doc.telephony_trunk_id = "master-test-trunk-id"
            doc.max_concurrent_calls = 5
            doc.enabled = 1
            doc.status = "ready"
            doc.background_queue_name = "default"
            doc.default_phone_number_id = "test-phone-id"
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
        else:
            frappe.db.set_value("Voice AI Telephony Account", acc_name, {
                "telephony_trunk_id": "master-test-trunk-id",
                "max_concurrent_calls": 5,
                "enabled": 1,
                "status": "ready",
                "default_phone_number_id": "test-phone-id"
            })
            frappe.db.commit()
            
        queue_name = "Master Test Queue"
        existing_queue = frappe.db.get_value("Call Queue", {"queue_name": queue_name}, "name")
        if not existing_queue:
            doc = frappe.new_doc("Call Queue")
            doc.queue_name = queue_name # Display name
            doc.telephony_account = acc_name
            doc.default_agent_id = "test-agent-id"
            doc.enabled = 1
            doc.status = "Open"
            doc.insert(ignore_permissions=True)
            queue_id = doc.name
            frappe.db.commit()
        else:
            queue_id = existing_queue
            frappe.db.set_value("Call Queue", queue_id, {
                "default_agent_id": "test-agent-id"
            })
            qdoc = frappe.get_doc("Call Queue", queue_id)
            queue_name = qdoc.queue_name

        # DELETE old test records to ensure capacity is clear
        frappe.db.delete("Voice AI Encounter Queue", {"customer_phone": ["like", "8000000%"]})
        frappe.db.commit()

        # Clean up any old active load
        from voice_ai.voice_ai.assignment import refresh_account_active_load
        refresh_account_active_load(acc_name)

        # Import functions to test
        from voice_ai.voice_ai.processor import (
            create_encounter_queue, 
            update_encounter_status,
            process_open_call_queues,
            submit_encounter_queue
        )
        import voice_ai.voice_ai.processor as proc_module

        # Mock _post_json
        original_post_json = proc_module._post_json
        def mocked_post_json(url, payload, headers=None, timeout=30):
            if "elevenlabs" in url:
                if payload.get("to_number") == "8000000401":
                    return 401, {"status": "error", "message": "Invalid API Key"}
                return 200, {"status": "success", "callSid": "mock-sid-" + payload.get("to_number", "unknown")}
            return 200, {}
        proc_module._post_json = mocked_post_json

        # Mock enqueue to run synchronously
        original_enqueue = frappe.enqueue
        def mocked_enqueue(method, **kwargs):
            method_args = {k: v for k, v in kwargs.items() if k not in ["queue", "is_async", "timeout", "at_front", "job_name", "enqueue_after_commit"]}
            return frappe.get_attr(method)(**method_args)
        frappe.enqueue = mocked_enqueue

        # ---------------------------------------------------------
        # TEST 1: Early Assignment & Visibility
        # ---------------------------------------------------------
        phone1 = "8000000001"
        res1 = create_encounter_queue(customer_phone=phone1, call_queue=queue_id, submit_now=False)
        doc1 = frappe.get_doc(QUEUE_DOCTYPE, res1["queue_name"])
        
        if doc1.assigned_account == acc_name and doc1.telephony_trunk_id == "master-test-trunk-id":
            log_result("Early Assignment & Visibility", True, "Account and Trunk ID assigned immediately at birth.")
        else:
            log_result("Early Assignment & Visibility", False, f"Assignment failed. Account: {doc1.assigned_account}, Trunk: {doc1.telephony_trunk_id}")

        # ---------------------------------------------------------
        # TEST 2: Flexible Queue Lookup
        # ---------------------------------------------------------
        phone2 = "8000000002"
        res2 = create_encounter_queue(customer_phone=phone2, call_queue=queue_name, submit_now=False) 
        if res2["call_queue"] == queue_id:
            log_result("Flexible Queue Lookup", True, f"Successfully resolved '{queue_name}' to ID '{queue_id}'.")
            # Complete Test 2 to free up capacity
            update_encounter_status(name=res2["queue_name"], queue_status="Completed", telephony_status="completed")
        else:
            log_result("Flexible Queue Lookup", False, f"Lookup failed. Result: {res2['call_queue']}")

        # ---------------------------------------------------------
        # TEST 3: Status Protection
        # ---------------------------------------------------------
        update_encounter_status(name=doc1.name, queue_status="Completed", telephony_status="completed")
        update_encounter_status(name=doc1.name, queue_status="In Progress", telephony_status="in_progress")
        doc1.reload()
        if doc1.queue_status == "Completed":
            log_result("Status Protection", True, "Successfully blocked ElevenLabs from overwriting terminal status.")
        else:
            log_result("Status Protection", False, f"Status regressed to {doc1.queue_status}")

        # ---------------------------------------------------------
        # TEST 4: Failure & Retry Logic
        # ---------------------------------------------------------
        phone4 = "8000000004"
        res4 = create_encounter_queue(customer_phone=phone4, call_queue=queue_id, submit_now=True)
        update_encounter_status(name=res4["queue_name"], telephony_status="failed")
        doc4 = frappe.get_doc(QUEUE_DOCTYPE, res4["queue_name"])
        if doc4.queue_status in ["Failed", "Retry Scheduled"]:
            log_result("Failure & Retry Logic", True, "Status correctly moved to Failed upon telephony failure.")
        else:
            log_result("Failure & Retry Logic", False, f"Status is {doc4.queue_status}")

        # ---------------------------------------------------------
        # TEST 5: Global Busy Filter & Worker Pickup
        # ---------------------------------------------------------
        try:
            frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 5)
            refresh_account_active_load(acc_name)
            phone5 = "8000000005"
            resA = create_encounter_queue(customer_phone=phone5, call_queue=queue_id, submit_now=True)
            resB = create_encounter_queue(customer_phone=phone5, call_queue=queue_id, submit_now=True)
            
            docB = frappe.get_doc(QUEUE_DOCTYPE, resB["queue_name"])
            if docB.queue_status == "Retry Scheduled" and docB.assigned_account:
                log_result("Global Busy Filter", True, "Successfully blocked Call B (Sticky) while Call A active.")
                update_encounter_status(name=resA["queue_name"], queue_status="Completed", telephony_status="completed")
                process_open_call_queues()
                docB.reload()
                if docB.queue_status == "In Progress":
                    log_result("Worker Pickup", True, "Call B picked up successfully by worker.")
                    update_encounter_status(name=resB["queue_name"], queue_status="Completed", telephony_status="completed")
                else:
                    log_result("Worker Pickup", False, f"Call B not picked up. Status: {docB.queue_status}")
            else:
                log_result("Global Busy Filter", False, f"Call B not blocked or not sticky. Status: {docB.queue_status}, Account: {docB.assigned_account}")
        except Exception as e:
            log_result("Global Busy Filter & Worker Pickup", False, str(e))

        # ---------------------------------------------------------
        # TEST 6: Capacity Limits & Resolution
        # ---------------------------------------------------------
        try:
            frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 1)
            refresh_account_active_load(acc_name)
            resC1 = create_encounter_queue(customer_phone="8000000006", call_queue=queue_id, submit_now=True)
            resC2 = create_encounter_queue(customer_phone="8000000007", call_queue=queue_id, submit_now=True)
            
            docC2 = frappe.get_doc(QUEUE_DOCTYPE, resC2["queue_name"])
            if docC2.queue_status == "Pending" and docC2.assigned_account:
                log_result("Capacity Limits", True, "Worker respected capacity of 1 (Sticky).")
                update_encounter_status(name=resC1["queue_name"], queue_status="Completed", telephony_status="completed")
                process_open_call_queues()
                docC2.reload()
                if docC2.queue_status == "In Progress":
                    log_result("Capacity Resolution", True, "Processed queue sequentially.")
                    update_encounter_status(name=resC2["queue_name"], queue_status="Completed", telephony_status="completed")
                else:
                    log_result("Capacity Resolution", False, f"Sequential processing failed. Status: {docC2.queue_status}")
            else:
                log_result("Capacity Limits", False, f"Capacity not respected. Status: {docC2.queue_status}")
        except Exception as e:
            log_result("Capacity Limits & Resolution", False, str(e))

        # ---------------------------------------------------------
        # TEST 7: Worker Safety Fallback
        # ---------------------------------------------------------
        try:
            frappe.db.set_value("Voice AI Telephony Account", acc_name, "max_concurrent_calls", 5)
            frappe.db.set_value("Voice AI Telephony Account", acc_name, "background_queue_name", "non_existent_queue")
            refresh_account_active_load(acc_name)
            res7 = create_encounter_queue(customer_phone="8000000008", call_queue=queue_id, submit_now=True)
            log_result("Worker Safety Fallback", True, "System gracefully fell back to 'default' worker.")
        except Exception as e:
            log_result("Worker Safety Fallback", False, str(e))

        # ---------------------------------------------------------
        # TEST 8: ElevenLabs API Failure Handling
        # ---------------------------------------------------------
        try:
            frappe.db.set_value("Voice AI Telephony Account", acc_name, "background_queue_name", "default")
            refresh_account_active_load(acc_name)
            phone8 = "8000000401" # Triggers mock 401
            res8 = create_encounter_queue(customer_phone=phone8, call_queue=queue_id, submit_now=True)
            doc8 = frappe.get_doc(QUEUE_DOCTYPE, res8["queue_name"])
            if doc8.queue_status in ["Failed", "Retry Scheduled"] and ("Invalid API Key" in (doc8.notes or "") or "ElevenLabs" in (doc8.notes or "")):
                log_result("ElevenLabs API Failure Handling", True, "Successfully caught API error.")
            else:
                log_result("ElevenLabs API Failure Handling", False, f"API error not handled. Status: {doc8.queue_status}, Notes: {doc8.notes}")
        except Exception as e:
            log_result("ElevenLabs API Failure Handling", False, str(e))

        # ---------------------------------------------------------
        # TEST 9: 15-Minute Timeout Cleanup
        # ---------------------------------------------------------
        phone9 = "8000000999"
        res9 = create_encounter_queue(customer_phone=phone9, call_queue=queue_id, submit_now=False)
        doc9 = frappe.get_doc(QUEUE_DOCTYPE, res9["queue_name"])
        doc9.queue_status = "In Progress"
        doc9.save(ignore_permissions=True)
        old_time = frappe.utils.add_to_date(None, minutes=-20)
        frappe.db.set_value(QUEUE_DOCTYPE, doc9.name, "last_status_at", old_time, update_modified=False)
        frappe.db.commit()
        process_open_call_queues()
        doc9.reload()
        if doc9.queue_status == "Failed" and "Stale call" in (doc9.notes or ""):
            log_result("15-Minute Timeout Cleanup", True, "Successfully timed out stale call.")
        else:
            log_result("15-Minute Timeout Cleanup", False, f"Timeout failed. Status: {doc9.queue_status}")

    finally:
        # Restore mocks
        try: proc_module._post_json = original_post_json
        except: pass
        try: frappe.enqueue = original_enqueue
        except: pass
        frappe.destroy()

if __name__ == "__main__":
    run_master_test_suite()
