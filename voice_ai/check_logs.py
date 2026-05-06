import frappe

def check_logs():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        logs = frappe.get_all("Voice AI Call", fields=["name", "telephony_account", "call_status"], limit=5)
        print(f"Found {len(logs)} logs.")
        for log in logs:
            print(log)
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_logs()
