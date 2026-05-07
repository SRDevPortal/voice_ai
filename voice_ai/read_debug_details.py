import frappe

def read_debug_log_details():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        logs = frappe.get_all("Error Log", 
            filters={"method": "Triple-Lock Debug"},
            order_by="creation desc",
            limit=5,
            fields=["creation", "error"]
        )
        for log in logs:
            print(f"Time: {log.creation}")
            print(f"DEBUG LOG:\n{log.error}")
            print("-" * 50)
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_debug_log_details()
