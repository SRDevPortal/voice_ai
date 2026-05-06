import frappe

def check_overrides():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Check for Property Setters
        setters = frappe.get_all("Property Setter", 
            filters={"doc_type": ["in", ["Voice AI Telephony Account", "Voice AI Encounter Queue"]]},
            fields=["name", "doc_type", "property", "value"]
        )
        print(f"Property Setters found: {setters}")

        # Check for Custom Fields
        custom_fields = frappe.get_all("Custom Field",
            filters={"dt": ["in", ["Voice AI Telephony Account", "Voice AI Encounter Queue"]]},
            fields=["name", "dt", "fieldname"]
        )
        print(f"Custom Fields found: {custom_fields}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_overrides()
