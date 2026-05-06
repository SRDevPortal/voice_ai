import frappe

def read_debug_logs():
    frappe.init(site="mysite.localhost")
    frappe.connect()
    try:
        # Check Error Log fields
        meta = frappe.get_meta("Error Log")
        fields = [f.fieldname for f in meta.fields]
        print(f"Error Log Fields: {fields}")
        
        # Try fetching with likely fields
        content_field = "text_content" if "text_content" in fields else "error"
        
        logs = frappe.get_all("Error Log", 
            filters={"title": "Triple-Lock Debug"},
            order_by="creation desc",
            limit=3,
            fields=["creation", "title", content_field]
        )
        for log in logs:
            print(f"Time: {log.creation}")
            print(f"Details:\n{log.get(content_field)}")
            print("-" * 50)
            
    finally:
        frappe.destroy()

if __name__ == "__main__":
    read_debug_logs()
