import frappe

def read_debug_logs():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        logs = frappe.get_all("Error Log", 
            filters={"method": "Triple-Lock Debug"},
            order_by="creation desc",
            limit=3,
            fields=["creation", "method", "error"]
        )
        for log in logs:
            print(f"Time: {log.creation}")
            print(f"Details:\n{log.error}")
            print("-" * 50)
            
        if not logs:
            print("No Triple-Lock Debug logs found. Is the filter correct?")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_debug_logs()
