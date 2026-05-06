import frappe

def read_debug_logs():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        logs = frappe.get_all("Error Log", 
            filters={"title": "Triple-Lock Debug"},
            order_by="creation desc",
            limit=3,
            fields=["creation", "message"]
        )
        for log in logs:
            print(f"Time: {log.creation}")
            print(f"Details:\n{log.message}")
            print("-" * 50)
            
        if not logs:
            print("No Triple-Lock Debug logs found. Did the request reach Frappe?")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_debug_logs()
