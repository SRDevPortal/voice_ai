import frappe
import json

def check_failed():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        if frappe.db.exists("Voice AI Encounter Queue", "rib6injmqo"):
            doc = frappe.get_doc("Voice AI Encounter Queue", "rib6injmqo")
            print(json.dumps(doc.as_dict(), indent=2, default=str))
        else:
            print("Record rib6injmqo not found")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_failed()
