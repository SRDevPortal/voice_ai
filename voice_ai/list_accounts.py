import frappe

def list_accounts():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        accounts = frappe.get_all("Voice AI Telephony Account", fields=["name", "enabled", "status", "max_concurrent_calls", "telephony_trunk_id"])
        print(f"Accounts: {accounts}")
        
        # Check the Call Queue as well
        queues = frappe.get_all("Call Queue", fields=["name", "enabled", "status", "telephony_account"])
        print(f"Call Queues: {queues}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    list_accounts()
