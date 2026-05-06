import frappe
from frappe.utils import getdate

def create_fiscal_year():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    fiscal_year = "2026-2027"
    start_date = "2026-04-01"
    end_date = "2027-03-31"

    try:
        if not frappe.db.exists("Fiscal Year", fiscal_year):
            doc = frappe.get_doc({
                "doctype": "Fiscal Year",
                "year": fiscal_year,
                "year_start_date": start_date,
                "year_end_date": end_date
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"✅ Fiscal Year '{fiscal_year}' created successfully.")
        else:
            print(f"Fiscal Year '{fiscal_year}' already exists.")
            
        # Ensure it is set as default company fiscal year if needed
        # We'll just create the record for now as requested.
        
    except Exception as e:
        print(f"Error creating fiscal year: {e}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    create_fiscal_year()
