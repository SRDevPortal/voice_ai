import frappe

def check_final_result():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        name = "9g6e9leou6"
        res = frappe.db.get_value("Voice AI Encounter Queue", name, ["queue_status", "telephony_status"], as_dict=True)
        print(f"Record {name} Status: {res}")
        
        # Also check the last raw input log to confirm self-healing worked
        log = frappe.get_all("Error Log", filters={"method": "Triple-Lock Raw Input"}, order_by="creation desc", limit=1, fields=["error"])
        if log:
            print(f"Last Raw Log:\n{log[0].error}")
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_final_result()
