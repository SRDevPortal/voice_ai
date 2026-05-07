import frappe

def debug_create():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    
    print("Testing Account creation...")
    try:
        acc_name = "Master Test Line"
        if not frappe.db.exists("Voice AI Telephony Account", acc_name):
            doc = frappe.new_doc("Voice AI Telephony Account")
            doc.account_name = acc_name
            doc.telephony_trunk_id = "master-test-trunk-id"
            doc.max_concurrent_calls = 5
            doc.enabled = 1
            doc.status = "ready"
            doc.background_queue_name = "default"
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print("Successfully created Account")
        else:
            print("Account already exists")
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()
