import frappe

def check_settings():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        print("=== TELEPHONY ACCOUNTS ===")
        accounts = frappe.get_all("Voice AI Telephony Account", fields=["name", "enabled", "status", "max_concurrent_calls", "current_active_calls"])
        for acc in accounts:
            print(f"Name: {acc.name} | Enabled: {acc.enabled} | Status: {acc.status} | Max: {acc.max_concurrent_calls} | Current: {acc.current_active_calls}")
            
        print("\n=== CALL QUEUES ===")
        queues = frappe.get_all("Call Queue", fields=["name", "enabled", "status", "telephony_account"])
        for q in queues:
            print(f"Name: {q.name} | Enabled: {q.enabled} | Status: {q.status} | Account: {q.telephony_account}")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_settings()
