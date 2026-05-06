import frappe
from voice_ai.voice_ai.assignment import get_eligible_workers, get_worker_active_load

def test_assignment():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    try:
        call_queues = frappe.get_all("Call Queue", limit=1)
        if not call_queues:
            print("No call queues found.")
            return
        cq = call_queues[0].name

        workers = frappe.get_all("Voice AI Worker", limit=1)
        if not workers:
            w = frappe.get_doc({
                "doctype": "Voice AI Worker",
                "worker_name": "Test Worker",
                "enabled": 1,
                "auto_assign_enabled": 1,
                "status": "idle",
                "max_concurrent_calls": 1
            })
            w.append("allowed_queues", {"call_queue": cq})
            w.insert(ignore_permissions=True)
            worker_id = w.name
            print(f"Created worker {worker_id}")
        else:
            w = frappe.get_doc("Voice AI Worker", workers[0].name)
            w.max_concurrent_calls = 1
            if not any(row.call_queue == cq for row in w.allowed_queues):
                w.append("allowed_queues", {"call_queue": cq})
            w.save(ignore_permissions=True)
            worker_id = w.name
            print(f"Using worker {worker_id}")
        
        frappe.db.commit()

        eligible = get_eligible_workers(cq)
        print(f"Eligible workers for {cq} before load: {[x.name for x in eligible]}")

        # Create dummy load
        dummy = frappe.get_doc({
            "doctype": "Voice AI Encounter Queue",
            "call_queue": cq,
            "assigned_worker": worker_id,
            "queue_status": "Assigned"
        })
        dummy.insert(ignore_permissions=True)
        frappe.db.commit()

        load = get_worker_active_load(worker_id)
        print(f"Worker load after dummy: {load}")

        eligible_after = get_eligible_workers(cq)
        print(f"Eligible workers for {cq} after load: {[x.name for x in eligible_after]}")

        # Cleanup
        frappe.delete_doc("Voice AI Encounter Queue", dummy.name, ignore_permissions=True)
        frappe.db.commit()

    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_assignment()
