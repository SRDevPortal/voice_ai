import frappe

def check_scheduler_pulse():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("=== SCHEDULER HEARTBEAT (Last 10 Runs) ===")
        # Check the logs for our specific process
        logs = frappe.get_all("Scheduled Job Log", 
            filters={"scheduled_job_type": ["like", "%process_open_call_queues%"]},
            order_by="creation desc",
            limit=10,
            fields=["creation", "status"]
        )
        for log in logs:
            print(f"Time: {log.creation} | Status: {log.status}")
            
        if not logs:
            print("No Scheduled Job Logs found for 'process_open_call_queues'. Is the scheduler running?")
            
        print("\n=== CURRENT PENDING BATCH ===")
        pending_count = frappe.db.count("Voice AI Encounter Queue", {"queue_status": "Pending"})
        print(f"Total Pending Records right now: {pending_count}")
        
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_scheduler_pulse()
