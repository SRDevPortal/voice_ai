import frappe
from frappe.utils.password import update_password

def set_admin_password():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    try:
        if frappe.db.exists("User", "Administrator"):
            update_password("Administrator", "admin")
            frappe.db.commit()
            print("✅ Administrator password has been reset.")
        else:
            print("Administrator user not found.")
            
    except Exception as e:
        print(f"Error setting password: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    set_admin_password()
