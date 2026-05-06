import frappe
def check():
    patients = frappe.get_all("Patient", filters={"mobile": "9873362268"}, fields=["name", "patient_name"])
    for p in patients:
        print(f"ID: {p.name}, Name: {p.patient_name}")
