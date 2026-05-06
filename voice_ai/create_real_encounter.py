import frappe
from frappe.utils import now_datetime

def create_test_encounter():
    frappe.init(site="mysite.localhost")
    frappe.connect()

    try:
        phone = "9873362268"
        
        # 1. Find or Create Patient
        patient_name = frappe.db.get_value("Patient", {"mobile": phone}, "name")
        if not patient_name:
            patient = frappe.get_doc({
                "doctype": "Patient",
                "patient_name": "Test User Vishal",
                "mobile": phone,
                "sex": "Male",
                "status": "Active"
            })
            patient.insert(ignore_permissions=True)
            patient_name = patient.name
            print(f"Created Patient: {patient_name}")
        else:
            print(f"Found existing Patient: {patient_name}")

        # 2. Create Patient Encounter
        encounter = frappe.get_doc({
            "doctype": "Patient Encounter",
            "patient": patient_name,
            "patient_name": "Test User Vishal",
            "sr_pe_mobile": phone,
            "encounter_date": frappe.utils.today(),
            "encounter_time": frappe.utils.nowtime(),
            "sr_encounter_type": "Order",
            "sr_pe_deptt": "Skin",
            "sr_encounter_place": "Online",
            "company": frappe.db.get_value("Company", {}, "name") or "Sr Institute of Advanced Ayurvedic Sciences Private Limited",
            "sr_pe_order_items": [
                {
                    "doctype": "SR Order Item",
                    "sr_item_code": "SKIN-PSO-30",
                    "sr_item_name": "Skin PSO Treatment 30 Days",
                    "sr_item_amount": 4000,
                    "sr_item_qty": 1,
                    "sr_item_rate": 4000
                }
            ]
        })
        encounter.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"SUCCESS: Created Patient Encounter {encounter.name} for {phone}")

    finally:
        frappe.destroy()

if __name__ == "__main__":
    create_test_encounter()
