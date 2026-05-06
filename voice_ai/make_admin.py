import frappe

def make_system_manager():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    email = "admin@example.com"
    try:
        if not frappe.db.exists("User", email):
            print(f"User {email} does not exist in the database.")
            return

        user = frappe.get_doc("User", email)
        
        # Check if they already have System Manager
        has_role = any(role.role == "System Manager" for role in user.get("roles"))
        
        if not has_role:
            user.append("roles", {
                "doctype": "Has Role",
                "role": "System Manager"
            })
            user.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"✅ Successfully added 'System Manager' (Admin) role to {email}.")
        else:
            print(f"User {email} already has the 'System Manager' role.")
            
    except Exception as e:
        print(f"Error giving admin access: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    make_system_manager()
