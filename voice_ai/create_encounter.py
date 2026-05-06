import frappe

def create_encounter():
    patient_id = "HLC-PAT-2026-00004"
    phone = "9873362268"

    practitioners = frappe.get_all("Healthcare Practitioner", limit=1)
    practitioner = practitioners[0].name if practitioners else None

    encounter_data = {
        "doctype": "Patient Encounter",
        "patient": patient_id,
        "practitioner": practitioner,
        "company": frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company"),
        "sr_encounter_type": "Followup",
        "sr_encounter_place": "OPD"
    }

    encounter = frappe.get_doc(encounter_data)
    if frappe.get_meta("Patient Encounter").has_field("sr_pe_mobile"):
        encounter.sr_pe_mobile = phone
        
    encounter.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print(f"✅ Successfully created Patient Encounter: {encounter.name} for Patient: {patient_id}")

