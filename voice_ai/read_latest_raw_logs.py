import frappe

def read_latest_raw_logs():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        logs = frappe.get_all("Error Log", 
            filters={"method": "Triple-Lock Raw Input"},
            order_by="creation desc",
            limit=10,
            fields=["creation", "error"]
        )
        for log in logs:
            print(f"Time: {log.creation}")
            print(f"RAW INPUT RECEIVED:\n{log.error}")
            print("-" * 50)
            
        if not logs:
            print("No Triple-Lock Raw Input logs found for today.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_latest_raw_logs()
