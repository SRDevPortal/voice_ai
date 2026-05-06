import frappe

def grant_healthcare_and_keys():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    # The user we reset earlier
    user_id = "Administrator"

    try:
        if not frappe.db.exists("User", user_id):
            print("Administrator user not found.")
            return

        user = frappe.get_doc("User", user_id)
        
        # Add Healthcare Administrator role if not present
        has_role = any(role.role == "Healthcare Administrator" for role in user.get("roles"))
        if not has_role:
            user.append("roles", {
                "doctype": "Has Role",
                "role": "Healthcare Administrator"
            })
            
        # Add System Manager role if not present
        has_sys_manager = any(role.role == "System Manager" for role in user.get("roles"))
        if not has_sys_manager:
            user.append("roles", {
                "doctype": "Has Role",
                "role": "System Manager"
            })

        user.save(ignore_permissions=True)

        # Generate API Keys
        api_secret = frappe.generate_hash(length=15)
        user.api_key = frappe.generate_hash(length=15)
        user.api_secret = api_secret
        user.save(ignore_permissions=True)
        frappe.db.commit()

        print(f"✅ User: {user_id}")
        print(f"✅ API Key: {user.api_key}")
        print(f"✅ API Secret: {api_secret}")
        print("✅ Permissions: Granted 'Healthcare Administrator' and 'System Manager'")

    except Exception as e:
        print(f"Error granting permissions: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    grant_healthcare_and_keys()
