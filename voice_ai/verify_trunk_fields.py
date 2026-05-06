import frappe

def check_fields():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        meta = frappe.get_meta("Voice AI Encounter Queue")
        fieldnames = [f.fieldname for f in meta.fields]
        print(f"Fields in Encounter Queue: {fieldnames}")
        if "telephony_trunk_id" in fieldnames:
            print("SUCCESS: telephony_trunk_id exists!")
        else:
            print("FAILURE: telephony_trunk_id NOT FOUND!")
            
        # Check Account DocType too
        meta_acc = frappe.get_meta("Voice AI Telephony Account")
        fieldnames_acc = [f.fieldname for f in meta_acc.fields]
        print(f"Fields in Telephony Account: {fieldnames_acc}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_fields()
