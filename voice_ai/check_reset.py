import frappe

def check_bbutatk0u9():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        name = "bbutatk0u9"
        res = frappe.db.get_value("Voice AI Encounter Queue", name, ["customer_phone", "telephony_trunk_id", "queue_status"], as_dict=True)
        print(f"Record {name}: {res}")
        
        # If it's already Completed, the Triple-Lock will ignore it!
        # We need it to be in an active status for the test.
        if res.queue_status == "Completed":
            frappe.db.set_value("Voice AI Encounter Queue", name, "queue_status", "Assigned")
            frappe.db.commit()
            print("Reset record to Assigned for the audit test.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_bbutatk0u9()
