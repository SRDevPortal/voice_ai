"""Queue assignment helpers for Voice AI."""

from __future__ import annotations

import frappe

ACTIVE_ASSIGNMENT_STATUSES = {"Assigned", "Picked", "In Progress", "Retry Scheduled"}
ACTIVE_LOAD_STATUSES = {"Picked", "In Progress"}
ACTIVE_WORKER_STATUSES = {"idle", "ready", "busy"}

ACCOUNT_DOCTYPE = "Voice AI Telephony Account"

def get_account_active_load(account_name: str) -> int:
	return frappe.db.count(
		"Voice AI Encounter Queue",
		{
			"assigned_account": account_name,
			"queue_status": ["in", list(ACTIVE_LOAD_STATUSES)],
		},
	)

def refresh_account_active_load(account_name: str) -> int:
	load = get_account_active_load(account_name)
	if frappe.db.exists(ACCOUNT_DOCTYPE, account_name):
		frappe.db.set_value(ACCOUNT_DOCTYPE, account_name, "current_active_calls", load, update_modified=False)
	return load

def get_eligible_account(call_queue: str, ignore_capacity: bool = False) -> dict | None:
	if not call_queue:
		return None

	queue_data = frappe.db.get_value(
		"Call Queue",
		call_queue,
		["enabled", "status", "auto_assign_workers", "telephony_account"],
		as_dict=True,
	)
	if not queue_data or not queue_data.enabled or queue_data.status != "Open":
		return None
	
	if not queue_data.telephony_account:
		return None

	account = frappe.get_doc(ACCOUNT_DOCTYPE, queue_data.telephony_account)
	# Force reload to bypass cache and get real-time limits
	account.reload()
	
	if not account.enabled or account.status not in ACTIVE_WORKER_STATUSES:
		return None

	if not ignore_capacity:
		current_load = get_account_active_load(account.name)
		# FIX: Respect 0 as 0, default to 1 if null
		max_calls = int(account.max_concurrent_calls if account.max_concurrent_calls is not None else 1)
		
		if current_load >= max_calls:
			return None

	account_dict = account.as_dict()
	return account_dict

def is_phone_busy_globally(phone: str, current_doc_name: str | None = None) -> bool:
	"""Check if there is already an active call session for this phone number."""
	if not phone:
		return False
	
	from voice_ai.voice_ai.processor import normalize_phone_number
	normalized_phone = normalize_phone_number(phone)
	
	# Any status that implies the telephony line is occupied or about to be
	busy_statuses = ["Assigned", "Picked", "In Progress", "Retry Scheduled"]
	
	filters = {
		"customer_phone": ["like", f"%{normalized_phone}"],
		"queue_status": ["in", busy_statuses]
	}
	if current_doc_name:
		filters["name"] = ["!=", current_doc_name]
	
	return frappe.db.exists("Voice AI Encounter Queue", filters)

def assign_worker_to_queue_doc(queue_doc) -> str | None:
	"""Legacy named function, now assigns Telephony Account."""
	if not queue_doc.get("call_queue"):
		return None
	
	if not queue_doc.get("assigned_account"):
		# INITIAL ASSIGNMENT: Always assign at birth if possible, ignoring capacity
		eligible_account = get_eligible_account(queue_doc.call_queue, ignore_capacity=True)
		if eligible_account:
			queue_doc.assigned_account = eligible_account["name"]
			queue_doc.telephony_trunk_id = eligible_account.get("telephony_trunk_id")
			queue_doc.assigned_at = frappe.utils.now_datetime()
	
	if not queue_doc.assigned_account:
		return None

	# GLOBAL BUSY CHECK
	busy = is_phone_busy_globally(queue_doc.customer_phone, queue_doc.name)
	if busy:
		return None
		
	# CAPACITY CHECK
	account_data = frappe.db.get_value(ACCOUNT_DOCTYPE, queue_doc.assigned_account, ["enabled", "status", "max_concurrent_calls"], as_dict=True)
	if not account_data or not account_data.enabled or account_data.status not in ACTIVE_WORKER_STATUSES:
		return None

	current_load = get_account_active_load(queue_doc.assigned_account)
	max_calls = int(account_data.max_concurrent_calls if account_data.max_concurrent_calls is not None else 1)
	if current_load >= max_calls:
		return None

	refresh_account_active_load(queue_doc.assigned_account)
	
	if (queue_doc.get("queue_status") or "Pending") == "Pending":
		queue_doc.queue_status = "Assigned"
	
	queue_doc.assigned_agent = (
		queue_doc.get("assigned_agent")
		or frappe.db.get_value("Call Queue", queue_doc.call_queue, "default_agent_id")
	)

	return queue_doc.assigned_account
