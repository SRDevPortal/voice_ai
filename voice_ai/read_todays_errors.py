import frappe
from frappe.utils import nowdate

def read_todays_errors():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Check for any error log created today
        logs = frappe.get_all("Error Log", 
            filters={"creation": [">", nowdate()]},
            order_by="creation desc",
            limit=20,
            fields=["creation", "method", "error"]
        )
        for log in logs:
            print(f"Time: {log.creation} | Method: {log.method}")
            print(f"Error: {log.error[:500]}...") # Print first 500 chars
            print("-" * 50)
            
        if not logs:
            print("No Error Logs found for today (May 7th).")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_todays_errors()
