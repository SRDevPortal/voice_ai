import frappe

def sql_scan():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        query = "SELECT name, customer_phone, queue_status, telephony_trunk_id, modified FROM `tabVoice AI Encounter Queue` WHERE customer_phone LIKE '%86368%'"
        print(f"Executing: {query}")
        results = frappe.db.sql(query, as_dict=True)
        for r in results:
            print(f"ID: {r.name} | Phone: {r.customer_phone} | Status: {r.queue_status} | Trunk: {r.telephony_trunk_id} | Modified: {r.modified}")
            
        if not results:
            print("No records found in raw SQL.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    sql_scan()
