import frappe

def read_raw_input_logs():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        logs = frappe.get_all("Error Log", 
            filters={"method": "Triple-Lock Raw Input"},
            order_by="creation desc",
            limit=1,
            fields=["creation", "error"]
        )
        if logs:
            print(f"Time: {logs[0].creation}")
            print(f"RAW INPUT RECEIVED:\n{logs[0].error}")
        else:
            print("Still no 'Triple-Lock Raw Input' logs found. This is strange.")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_raw_input_logs()
