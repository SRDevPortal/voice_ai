from __future__ import annotations

import json
import socket
from datetime import time
from urllib import error, request
from urllib.parse import quote, urlencode

import frappe
from frappe.utils import add_to_date, cint, flt, get_datetime, get_time, now_datetime


QUEUE_DOCTYPE = "Voice AI Encounter Queue"
CALL_DOCTYPE = "Voice AI Call"
CALL_QUEUE_DOCTYPE = "Call Queue"
RETRY_DOCTYPE = "Voice AI Retry Policy"
ACTIVE_QUEUE_STATUSES = {"Picked", "In Progress", "Submitted"}
READY_QUEUE_STATUSES = {"Pending", "Assigned", "Retry Scheduled"}
NON_SUBMITTED_QUEUE_STATUSES = {"Pending", "Assigned", "Picked", "In Progress", "Retry Scheduled"}
RETRYABLE_TELEPHONY_STATUSES = {"busy", "no_answer", "timeout", "failed"}
TERMINAL_QUEUE_STATUSES = {"Completed", "Failed", "Escalated", "Closed"}


def get_elevenlabs_api_key() -> str | None:
	return frappe.conf.get("voice_ai_elevenlabs_api_key") or frappe.conf.get("elevenlabs_api_key")


def get_elevenlabs_base_url() -> str:
	return frappe.conf.get("voice_ai_elevenlabs_base_url") or "https://api.elevenlabs.io"


def get_elevenlabs_timeout() -> int:
	return cint(frappe.conf.get("voice_ai_elevenlabs_timeout") or 90)


def append_note(doc, note: str | None):
	if not note:
		return
	existing = (doc.notes or "").strip()
	line = f"[{now_datetime()}] {note.strip()}"
	doc.notes = f"{existing}\n{line}".strip() if existing else line


def normalize_phone_number(number: str | None) -> str | None:
	value = (number or "").strip()
	if not value:
		return None
	if value.startswith("+"):
		return value
	digits = "".join(ch for ch in value if ch.isdigit())
	if not digits:
		return None
	if len(digits) == 10:
		return f"+91{digits}"
	if len(digits) > 10:
		return f"+{digits}"
	return value


def get_default_call_queue() -> str | None:
	configured_queue = frappe.conf.get("voice_ai_default_call_queue")
	if configured_queue and frappe.db.exists(
		CALL_QUEUE_DOCTYPE, {"name": configured_queue, "enabled": 1, "status": "Open"}
	):
		return configured_queue

	row = frappe.get_all(
		CALL_QUEUE_DOCTYPE,
		filters={"enabled": 1, "status": "Open"},
		fields=["name", "priority", "modified"],
		order_by="priority asc, modified asc",
		limit=1,
	)
	return row[0].name if row else None


def get_patient_context(encounter_doc) -> dict:
	patient = encounter_doc.get("patient")
	patient_mobile = encounter_doc.get("sr_pe_mobile")
	customer = encounter_doc.get("customer")

	if patient:
		patient_values = frappe.db.get_value(
			"Patient",
			patient,
			["mobile", "customer"],
			as_dict=True,
		) or {}
		patient_mobile = patient_mobile or patient_values.get("mobile")
		customer = customer or patient_values.get("customer")

	return {
		"patient": patient,
		"patient_name": encounter_doc.get("patient_name"),
		"customer": customer,
		"customer_name": encounter_doc.get("patient_name"),
		"customer_phone": normalize_phone_number(patient_mobile),
		"company": encounter_doc.get("company"),
	}


def get_existing_open_queue(patient_encounter: str) -> str | None:
	return frappe.db.get_value(
		QUEUE_DOCTYPE,
		{
			"patient_encounter": patient_encounter,
			"queue_status": ["in", list(NON_SUBMITTED_QUEUE_STATUSES)],
		},
		"name",
	)


def build_queue_response(queue_doc, created: bool, reused: bool) -> dict:
	return {
		"ok": True,
		"created": created,
		"reused": reused,
		"queue_name": queue_doc.name,
		"patient_encounter": queue_doc.patient_encounter,
		"call_queue": queue_doc.call_queue,
		"queue_status": queue_doc.queue_status,
		"telephony_status": queue_doc.telephony_status,
		"customer_phone": queue_doc.customer_phone,
		"session_id": queue_doc.session_id,
	}


def _json_payload_from_string(value):
	if not value:
		return None
	if isinstance(value, dict):
		return value
	try:
		return json.loads(value)
	except Exception:
		return {"raw": value}


def _append_api_note(queue_doc, note: str | None):
	if note:
		append_note(queue_doc, f"n8n API: {note}")


def _post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 30):
	data = json.dumps(payload).encode("utf-8")
	req = request.Request(
		url,
		data=data,
		headers={"Content-Type": "application/json", **(headers or {})},
		method="POST",
	)
	try:
		with request.urlopen(req, timeout=timeout) as response:
			body = response.read().decode("utf-8")
			return response.status, json.loads(body) if body else {}
	except error.HTTPError as exc:
		body = exc.read().decode("utf-8") if exc.fp else ""
		try:
			parsed = json.loads(body) if body else {}
		except Exception:
			parsed = {"raw": body}
		return exc.code, parsed


def _get_json(url: str, headers: dict | None = None, timeout: int = 30):
	req = request.Request(url, headers=headers or {}, method="GET")
	try:
		with request.urlopen(req, timeout=timeout) as response:
			body = response.read().decode("utf-8")
			return response.status, json.loads(body) if body else {}
	except error.HTTPError as exc:
		body = exc.read().decode("utf-8") if exc.fp else ""
		try:
			parsed = json.loads(body) if body else {}
		except Exception:
			parsed = {"raw": body}
		return exc.code, parsed


def _log_remote_error(message: str, details: dict | None = None):
	payload = {"message": message, **(details or {})}
	frappe.log_error(json.dumps(payload, default=str, indent=2), "Voice AI Remote Frappe Fetch Failed")


def _remote_base_url(remote_site_url: str | None) -> str:
	return (remote_site_url or "").strip().rstrip("/")


def get_remote_headers(api_key: str | None, api_secret: str | None) -> dict:
	return {
		"Accept": "application/json",
		"Authorization": f"token {(api_key or '').strip()}:{(api_secret or '').strip()}",
		"User-Agent": "Mozilla/5.0 VoiceAI-Frappe-Integration/1.0",
	}


def remote_get(remote_site_url: str, api_key: str, api_secret: str, doctype: str, name: str, timeout: int = 30) -> dict:
	url = f"{_remote_base_url(remote_site_url)}/api/resource/{quote(doctype)}/{quote(name)}"
	status_code, response = _get_json(url, headers=get_remote_headers(api_key, api_secret), timeout=timeout)
	if status_code >= 400:
		_log_remote_error(
			f"Remote GET failed for {doctype} {name}",
			{"url": url, "status_code": status_code, "response": response},
		)
		raise frappe.ValidationError(f"Remote Frappe fetch failed for {doctype} {name} with status {status_code}")
	return response.get("data") if isinstance(response, dict) else {}


def remote_get_list(
	remote_site_url: str,
	api_key: str,
	api_secret: str,
	doctype: str,
	filters: dict,
	fields: list[str],
	order_by: str | None = None,
	limit_page_length: int | None = None,
	timeout: int = 30,
) -> list[dict]:
	params = {
		"filters": json.dumps(filters),
		"fields": json.dumps(fields),
	}
	if order_by:
		params["order_by"] = order_by
	if limit_page_length:
		params["limit_page_length"] = str(limit_page_length)
	url = f"{_remote_base_url(remote_site_url)}/api/resource/{quote(doctype)}?{urlencode(params)}"
	status_code, response = _get_json(url, headers=get_remote_headers(api_key, api_secret), timeout=timeout)
	if status_code >= 400:
		_log_remote_error(
			f"Remote list fetch failed for {doctype}",
			{"url": url, "filters": filters, "status_code": status_code, "response": response},
		)
		raise frappe.ValidationError(f"Remote Frappe list fetch failed for {doctype} with status {status_code}")
	return response.get("data") if isinstance(response, dict) else []


def format_address(address_doc) -> str:
	parts = [
		address_doc.get("address_line1"),
		address_doc.get("address_line2"),
		address_doc.get("city"),
		address_doc.get("state"),
		address_doc.get("pincode"),
		address_doc.get("country"),
	]
	return ", ".join(str(part).strip() for part in parts if str(part or "").strip())


def get_linked_address(doctype: str, name: str | None) -> str:
	if not name:
		return ""

	if doctype == "Customer":
		customer_address = frappe.db.get_value("Customer", name, "customer_primary_address")
		if customer_address and frappe.db.exists("Address", customer_address):
			return format_address(frappe.get_doc("Address", customer_address))

	links = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Address", "link_doctype": doctype, "link_name": name},
		fields=["parent"],
		order_by="modified desc",
		limit=20,
	)
	for link in links:
		if frappe.db.get_value("Address", link.parent, "is_primary_address"):
			return format_address(frappe.get_doc("Address", link.parent))

	if links:
		return format_address(frappe.get_doc("Address", links[0].parent))

	return ""


def get_remote_linked_address(remote_config: dict, doctype: str, name: str | None) -> str:
	if not name:
		return ""

	if doctype == "Customer":
		customer_doc = remote_get(
			remote_config["remote_site_url"],
			remote_config["api_key"],
			remote_config["api_secret"],
			"Customer",
			name,
		)
		customer_address = customer_doc.get("customer_primary_address")
		if customer_address:
			address_doc = remote_get(
				remote_config["remote_site_url"],
				remote_config["api_key"],
				remote_config["api_secret"],
				"Address",
				customer_address,
			)
			return format_address(address_doc)

	links = remote_get_list(
		remote_config["remote_site_url"],
		remote_config["api_key"],
		remote_config["api_secret"],
		"Dynamic Link",
		{"parenttype": "Address", "link_doctype": doctype, "link_name": name},
		["parent"],
		order_by="modified desc",
		limit_page_length=20,
	)
	for link in links:
		address_doc = remote_get(
			remote_config["remote_site_url"],
			remote_config["api_key"],
			remote_config["api_secret"],
			"Address",
			link.get("parent"),
		)
		if address_doc.get("is_primary_address"):
			return format_address(address_doc)

	if links:
		address_doc = remote_get(
			remote_config["remote_site_url"],
			remote_config["api_key"],
			remote_config["api_secret"],
			"Address",
			links[0].get("parent"),
		)
		return format_address(address_doc)

	return ""


def get_remote_patient_context(remote_config: dict, encounter_doc: dict) -> dict:
	patient = encounter_doc.get("patient")
	patient_mobile = encounter_doc.get("sr_pe_mobile")
	customer = encounter_doc.get("customer")

	if patient:
		patient_doc = remote_get(
			remote_config["remote_site_url"],
			remote_config["api_key"],
			remote_config["api_secret"],
			"Patient",
			patient,
		)
		patient_mobile = patient_mobile or patient_doc.get("mobile")
		customer = customer or patient_doc.get("customer")

	return {
		"patient": patient,
		"patient_name": encounter_doc.get("patient_name"),
		"customer": customer,
		"customer_name": encounter_doc.get("patient_name"),
		"customer_phone": normalize_phone_number(patient_mobile),
	}


def safe_get_remote_linked_address(remote_config: dict, doctype: str, name: str | None) -> str:
	try:
		return get_remote_linked_address(remote_config, doctype, name)
	except Exception as exc:
		_log_remote_error(
			f"Remote address fetch failed for {doctype} {name}",
			{"doctype": doctype, "name": name, "error": str(exc), "traceback": frappe.get_traceback()},
		)
		return ""


def build_remote_encounter_context(queue_doc, remote_config: dict) -> dict:
	patient_encounter = queue_doc.patient_encounter
	if not patient_encounter:
		raise frappe.ValidationError(f"Encounter Queue {queue_doc.name} has no patient encounter reference")

	encounter_doc = remote_get(
		remote_config["remote_site_url"],
		remote_config["api_key"],
		remote_config["api_secret"],
		"Patient Encounter",
		patient_encounter,
	)
	patient_context = get_remote_patient_context(remote_config, encounter_doc)

	order_items = []
	order_total = 0.0
	for row in encounter_doc.get("sr_pe_order_items") or []:
		qty = flt(row.get("sr_item_qty") or 0)
		rate = flt(row.get("sr_item_rate") or 0)
		amount = flt(qty * rate)
		order_total += amount
		order_items.append(
			{
				"item_code": row.get("sr_item_code"),
				"item_name": row.get("sr_item_name"),
				"qty": qty,
				"rate": rate,
				"amount": amount,
			}
		)

	paid_total = 0.0
	for row in encounter_doc.get("enc_multi_payments") or []:
		paid_total += flt(row.get("mmp_paid_amount") or 0)

	order_items_text = ", ".join(
		f"{item.get('item_name') or item.get('item_code') or 'Item'} x {item['qty']:g} @ {item['rate']:g} = {item['amount']:g}"
		for item in order_items
	)
	patient = patient_context.get("patient") or encounter_doc.get("patient")
	customer = patient_context.get("customer") or encounter_doc.get("customer")
	address = safe_get_remote_linked_address(remote_config, "Patient", patient) or safe_get_remote_linked_address(
		remote_config, "Customer", customer
	)
	outstanding_amount = max(flt(order_total - paid_total), 0.0)

	return {
		"queue_name": queue_doc.call_queue,
		"queue_item": queue_doc.name,
		"session_id": queue_doc.session_id,
		"patient_encounter": patient_encounter,
		"patient": patient or "",
		"patient_name": patient_context.get("patient_name") or "",
		"customer": customer or "",
		"customer_name": patient_context.get("customer_name") or "",
		"customer_phone": normalize_phone_number(queue_doc.customer_phone or patient_context.get("customer_phone")),
		"order_id": queue_doc.order_id or "",
		"order_items": order_items_text,
		"payment_status": encounter_doc.get("payment_status") or "",
		"outstanding_amount": outstanding_amount,
		"amount": outstanding_amount,
		"address": address,
		"source_system": queue_doc.source_system or "",
	}


def _finalize_submission_failure(
	queue_doc,
	reason: str,
	policy: dict | None = None,
	request_payload: dict | None = None,
	response_payload: dict | None = None,
):
	queue_doc.telephony_status = "failed"
	queue_doc.last_status_at = now_datetime()
	queue_doc.last_status_change_source = "Queue Processor"
	policy = policy or get_retry_policy(queue_doc.retry_policy)
	if should_retry(queue_doc, policy):
		schedule_retry(queue_doc, policy=policy, reason=reason)
	else:
		queue_doc.queue_status = "Failed"
		queue_doc.ended_at = queue_doc.ended_at or now_datetime()
		append_note(queue_doc, reason)

	queue_doc.flags.ignore_permissions = True
	queue_doc.save(ignore_permissions=True)
	sync_call_log(queue_doc, request_payload=request_payload, response_payload=response_payload)
	frappe.db.commit()


def is_queue_callable_now(queue_doc) -> bool:
	now_value = get_time(now_datetime())
	start = queue_doc.get("allowed_calling_from")
	end = queue_doc.get("allowed_calling_till")
	if not start and not end:
		return True

	start_time = get_time(start) if start else time.min
	end_time = get_time(end) if end else time.max
	if start_time == time.min and end_time == time.min:
		return True
	start_seconds = (start_time.hour * 3600) + (start_time.minute * 60) + start_time.second
	end_seconds = (end_time.hour * 3600) + (end_time.minute * 60) + end_time.second
	if abs(start_seconds - end_seconds) <= 60:
		return True
	if start_time <= end_time:
		return start_time <= now_value <= end_time
	return now_value >= start_time or now_value <= end_time


def get_retry_policy(policy_name: str | None) -> dict:
	if not policy_name:
		return {}
	return frappe.db.get_value(
		RETRY_DOCTYPE,
		policy_name,
		[
			"enabled",
			"max_attempts",
			"first_retry_delay_mins",
			"subsequent_retry_delay_mins",
			"retry_on_busy",
			"retry_on_no_answer",
			"retry_on_failed",
			"retry_on_unclear_outcome",
			"stop_on_submitted",
		],
		as_dict=True,
	) or {}


def build_encounter_order_context(queue_doc) -> dict:
	if not queue_doc.patient_encounter or not frappe.db.exists("Patient Encounter", queue_doc.patient_encounter):
		return {
			"order_items": "",
			"payment_status": "",
			"outstanding_amount": 0.0,
			"address": "",
		}

	encounter_doc = frappe.get_doc("Patient Encounter", queue_doc.patient_encounter)
	order_items = []
	order_total = 0.0
	for row in encounter_doc.get("sr_pe_order_items") or []:
		qty = flt(row.get("sr_item_qty") or 0)
		rate = flt(row.get("sr_item_rate") or 0)
		amount = flt(qty * rate)
		order_total += amount
		order_items.append(
			{
				"item_code": row.get("sr_item_code"),
				"item_name": row.get("sr_item_name"),
				"qty": qty,
				"rate": rate,
				"amount": amount,
				}
			)

	paid_total = 0.0
	for row in encounter_doc.get("enc_multi_payments") or []:
		paid_total += flt(row.get("mmp_paid_amount") or 0)

	order_items_text = ", ".join(
		f"{item.get('item_name') or item.get('item_code') or 'Item'} x {item['qty']:g} @ {item['rate']:g} = {item['amount']:g}"
		for item in order_items
	)
	address = get_linked_address("Patient", encounter_doc.get("patient")) or get_linked_address(
		"Customer", queue_doc.customer or encounter_doc.get("customer")
	)

	return {
		"order_items": order_items_text,
		"payment_status": encounter_doc.get("payment_status") or "",
		"outstanding_amount": max(flt(order_total - paid_total), 0.0),
		"address": address,
	}


def build_dynamic_variables(queue_doc, remote_context: dict | None = None) -> dict:
	if remote_context:
		return remote_context

	encounter_context = build_encounter_order_context(queue_doc)
	return {
		"queue_name": queue_doc.call_queue,
		"queue_item": queue_doc.name,
		"session_id": queue_doc.session_id,
		"patient_encounter": queue_doc.patient_encounter,
		"patient": queue_doc.patient or "",
		"patient_name": queue_doc.patient_name or "",
		"customer": queue_doc.customer or "",
		"customer_name": queue_doc.customer_name or "",
		"customer_phone": queue_doc.customer_phone or "",
		"order_id": queue_doc.order_id or "",
		"order_items": encounter_context["order_items"],
		"payment_status": encounter_context["payment_status"],
		"outstanding_amount": encounter_context["outstanding_amount"],
		"amount": encounter_context["outstanding_amount"],
		"address": encounter_context["address"],
		"source_system": queue_doc.source_system or "",
	}


def build_elevenlabs_payload(queue_doc, queue_settings: dict, remote_context: dict | None = None) -> dict:
	agent_id = queue_settings.get("default_agent_id")
	phone_number_id = queue_settings.get("default_phone_number_id")
	to_number = normalize_phone_number(
		(remote_context or {}).get("customer_phone") if remote_context else queue_doc.customer_phone
	)

	if not agent_id:
		raise frappe.ValidationError(f"Call Queue {queue_doc.call_queue} is missing Default Agent ID")
	if not phone_number_id:
		raise frappe.ValidationError(f"Call Queue {queue_doc.call_queue} is missing Default Phone Number ID")
	if not to_number:
		raise frappe.ValidationError(f"Encounter Queue {queue_doc.name} has no callable customer phone")

	return {
		"agent_id": agent_id,
		"agent_phone_number_id": phone_number_id,
		"to_number": to_number,
		"conversation_initiation_client_data": {
			"dynamic_variables": build_dynamic_variables(queue_doc, remote_context=remote_context),
			"source_info": {"source": "sip_trunk", "version": "voice_ai"},
		},
	}


def sync_call_log(queue_doc, request_payload: dict | None = None, response_payload: dict | None = None):
	call_name = frappe.db.get_value(
		CALL_DOCTYPE,
		{"encounter_queue": queue_doc.name, "attempt_no": queue_doc.attempt_no},
	)
	call_doc = frappe.get_doc(CALL_DOCTYPE, call_name) if call_name else frappe.new_doc(CALL_DOCTYPE)
	call_doc.call_queue = queue_doc.call_queue
	call_doc.encounter_queue = queue_doc.name
	call_doc.patient_encounter = queue_doc.patient_encounter
	call_doc.attempt_no = queue_doc.attempt_no
	call_doc.to_number = normalize_phone_number(queue_doc.customer_phone)
	call_doc.call_status = queue_doc.telephony_status or "queued"
	call_doc.session_id = queue_doc.session_id
	call_doc.elevenlabs_conversation_id = queue_doc.elevenlabs_conversation_id
	call_doc.job_id = queue_doc.job_id
	call_doc.summary = queue_doc.summary
	call_doc.business_outcome = queue_doc.business_outcome
	if request_payload is not None:
		call_doc.request_payload = json.dumps(request_payload, default=str)
	if response_payload is not None:
		call_doc.response_payload = json.dumps(response_payload, default=str)
	call_doc.flags.ignore_permissions = True
	call_doc.save(ignore_permissions=True)
	return call_doc.name


def schedule_retry(queue_doc, policy: dict | None = None, reason: str | None = None):
	policy = policy or get_retry_policy(queue_doc.retry_policy)
	max_attempts = cint((policy or {}).get("max_attempts") or queue_doc.max_attempts or 0)
	queue_doc.max_attempts = max_attempts
	queue_doc.retry_count = max(cint(queue_doc.retry_count or 0), cint(queue_doc.attempt_no or 0))

	if max_attempts and cint(queue_doc.attempt_no or 0) >= max_attempts:
		queue_doc.queue_status = "Closed"
		queue_doc.business_outcome = queue_doc.business_outcome or "max_attempts_reached"
		queue_doc.telephony_status = "failed"
		queue_doc.ended_at = queue_doc.ended_at or now_datetime()
		queue_doc.next_retry_at = None
		if reason:
			append_note(queue_doc, f"Retry limit reached: {reason}")
		return

	delay = cint((policy or {}).get("first_retry_delay_mins") or 0)
	if cint(queue_doc.retry_count or 0) > 1:
		delay = cint((policy or {}).get("subsequent_retry_delay_mins") or delay or 0)
	delay = delay or 5

	queue_doc.queue_status = "Retry Scheduled"
	queue_doc.telephony_status = "retry_scheduled"
	queue_doc.next_retry_at = add_to_date(now_datetime(), minutes=delay)
	queue_doc.last_status_change_source = "Retry Scheduler"
	if reason:
		append_note(queue_doc, f"Retry scheduled in {delay} mins: {reason}")


def should_retry(queue_doc, policy: dict | None = None) -> bool:
	policy = policy or get_retry_policy(queue_doc.retry_policy)
	status = (queue_doc.telephony_status or "").strip().lower()
	if status == "busy":
		return bool(cint((policy or {}).get("retry_on_busy") or 0))
	if status == "no_answer":
		return bool(cint((policy or {}).get("retry_on_no_answer") or 0))
	if status == "failed":
		return bool(cint((policy or {}).get("retry_on_failed") or 0))
	if queue_doc.business_outcome == "unclear":
		return bool(cint((policy or {}).get("retry_on_unclear_outcome") or 0))
	return status == "timeout"


def get_call_queue_remote_config(call_queue: str) -> dict:
	call_queue_doc = frappe.get_doc(CALL_QUEUE_DOCTYPE, call_queue)
	return {
		"remote_access": bool(cint(call_queue_doc.get("remote_access") or 0)),
		"remote_site_url": call_queue_doc.get("remote_site_url"),
		"api_key": call_queue_doc.get_password("api_key") if call_queue_doc.get("api_key") else None,
		"api_secret": call_queue_doc.get_password("api_secret") if call_queue_doc.get("api_secret") else None,
	}


def validate_remote_config(remote_config: dict, call_queue: str):
	if not remote_config.get("remote_access"):
		return
	missing = [
		label
		for label, fieldname in (
			("Remote Site URL", "remote_site_url"),
			("API Key", "api_key"),
			("API Secret", "api_secret"),
		)
		if not remote_config.get(fieldname)
	]
	if missing:
		message = f"Call Queue {call_queue} has Remote Access enabled but is missing: {', '.join(missing)}"
		_log_remote_error(message, {"call_queue": call_queue, "missing": missing})
		raise frappe.ValidationError(message)


def submit_encounter_queue(queue_name: str, timeout: int | None = None) -> dict:
	queue_doc = frappe.get_doc(QUEUE_DOCTYPE, queue_name)
	queue_settings = frappe.db.get_value(
		CALL_QUEUE_DOCTYPE,
		queue_doc.call_queue,
		[
			"default_agent_id",
			"default_phone_number_id",
			"retry_policy",
			"queue_name",
		],
		as_dict=True,
	) or {}
	remote_config = get_call_queue_remote_config(queue_doc.call_queue)
	api_key = get_elevenlabs_api_key()
	if not api_key:
		raise frappe.ValidationError(
			"Missing ElevenLabs API key. Set voice_ai_elevenlabs_api_key or elevenlabs_api_key in site config."
		)

	if not queue_doc.retry_policy and queue_settings.get("retry_policy"):
		queue_doc.retry_policy = queue_settings["retry_policy"]
	timeout = cint(timeout or get_elevenlabs_timeout() or 90)
	policy = get_retry_policy(queue_doc.retry_policy)

	queue_doc.attempt_no = cint(queue_doc.attempt_no or 0) + 1
	queue_doc.picked_at = queue_doc.picked_at or now_datetime()
	queue_doc.last_status_at = now_datetime()
	queue_doc.last_status_change_source = "Queue Processor"
	queue_doc.queue_status = "Picked"

	remote_context = None
	try:
		validate_remote_config(remote_config, queue_doc.call_queue)
		if remote_config.get("remote_access"):
			remote_context = build_remote_encounter_context(queue_doc, remote_config)
	except Exception as exc:
		_log_remote_error(
			f"Remote context fetch failed for Encounter Queue {queue_doc.name}",
			{"queue_name": queue_doc.name, "call_queue": queue_doc.call_queue, "error": str(exc), "traceback": frappe.get_traceback()},
		)
		_finalize_submission_failure(
			queue_doc,
			reason=f"Remote Frappe fetch failed: {exc}",
			policy=policy,
			request_payload={"remote_access": True, "remote_site_url": remote_config.get("remote_site_url")},
			response_payload={"error": str(exc), "type": exc.__class__.__name__},
		)
		raise frappe.ValidationError(f"Remote Frappe fetch failed: {exc}") from exc

	payload = build_elevenlabs_payload(queue_doc, queue_settings, remote_context=remote_context)
	endpoint = f"{get_elevenlabs_base_url().rstrip('/')}/v1/convai/sip-trunk/outbound-call"
	try:
		status_code, response = _post_json(endpoint, payload, headers={"xi-api-key": api_key}, timeout=timeout)
	except (TimeoutError, socket.timeout) as exc:
		_finalize_submission_failure(
			queue_doc,
			reason=f"ElevenLabs request timed out after {timeout}s",
			policy=policy,
			request_payload=payload,
			response_payload={"error": str(exc), "type": exc.__class__.__name__},
		)
		raise frappe.ValidationError(f"ElevenLabs request timed out after {timeout}s") from exc
	except error.URLError as exc:
		reason = f"ElevenLabs network error: {exc.reason}"
		_finalize_submission_failure(
			queue_doc,
			reason=reason,
			policy=policy,
			request_payload=payload,
			response_payload={"error": str(exc), "type": exc.__class__.__name__},
		)
		raise frappe.ValidationError(reason) from exc

	queue_doc.job_id = (
		(response.get("callSid") if isinstance(response, dict) else None)
		or (response.get("call_id") if isinstance(response, dict) else None)
		or (response.get("sip_call_id") if isinstance(response, dict) else None)
		or queue_doc.job_id
	)
	queue_doc.elevenlabs_conversation_id = (
		(response.get("conversation_id") if isinstance(response, dict) else None)
		or queue_doc.elevenlabs_conversation_id
	)

	if status_code >= 400:
		reason = f"ElevenLabs submission failed with status {status_code}"
		_finalize_submission_failure(
			queue_doc,
			reason=reason,
			policy=policy,
			request_payload=payload,
			response_payload=response,
		)
	else:
		queue_doc.telephony_status = "dialing"
		queue_doc.queue_status = "In Progress"
		queue_doc.started_at = queue_doc.started_at or now_datetime()
		queue_doc.last_status_at = now_datetime()
		append_note(
			queue_doc,
			f"Submitted to ElevenLabs for {payload['to_number']} via queue {queue_settings.get('queue_name') or queue_doc.call_queue}",
		)

	queue_doc.flags.ignore_permissions = True
	queue_doc.save(ignore_permissions=True)
	sync_call_log(queue_doc, request_payload=payload, response_payload=response)
	frappe.db.commit()

	if status_code >= 400:
		raise frappe.ValidationError(f"ElevenLabs outbound submission failed with status {status_code}: {response}")

	return {
		"ok": True,
		"queue_name": queue_doc.name,
		"call_queue": queue_doc.call_queue,
		"status_code": status_code,
		"job_id": queue_doc.job_id,
		"conversation_id": queue_doc.elevenlabs_conversation_id,
	}


def get_due_queue_items(call_queue: str) -> dict[str, list[str]]:
	now_value = get_datetime(now_datetime())
	fresh_rows = frappe.get_all(
		QUEUE_DOCTYPE,
		filters={
			"call_queue": call_queue,
			"queue_status": ["in", ["Pending", "Assigned"]],
		},
		fields=["name", "creation"],
		order_by="creation asc",
	)

	retry_rows = frappe.get_all(
		QUEUE_DOCTYPE,
		filters={
			"call_queue": call_queue,
			"queue_status": "Retry Scheduled",
		},
		fields=["name", "next_retry_at", "creation"],
		order_by="creation asc",
	)

	due_retries = []
	waiting_retries = []
	for row in retry_rows:
		if row.next_retry_at and get_datetime(row.next_retry_at) > now_value:
			waiting_retries.append(row.name)
			continue
		due_retries.append(row.name)

	return {
		"fresh": [row.name for row in fresh_rows],
		"due_retries": due_retries,
		"waiting_retries": waiting_retries,
	}


def process_call_queue(call_queue: str) -> dict:
	queue_doc = frappe.get_doc(CALL_QUEUE_DOCTYPE, call_queue)
	if not queue_doc.enabled or queue_doc.status != "Open":
		return {"queue": call_queue, "processed": 0, "reason": "queue_not_open"}
	if not is_queue_callable_now(queue_doc):
		return {"queue": call_queue, "processed": 0, "reason": "outside_calling_window"}

	ready_items = get_due_queue_items(call_queue)
	dispatch_items = [*ready_items["fresh"], *ready_items["due_retries"]]
	processed = []
	errors = []
	for queue_name in dispatch_items:
		try:
			result = submit_encounter_queue(queue_name)
			processed.append(result["queue_name"])
		except Exception as exc:
			errors.append({"queue_name": queue_name, "error": str(exc)})
			frappe.log_error(frappe.get_traceback(), f"voice_ai queue processor failed for {queue_name}")

	return {
		"queue": call_queue,
		"processed": len(processed),
		"processed_items": processed,
		"fresh_items": ready_items["fresh"],
		"due_retry_items": ready_items["due_retries"],
		"waiting_retry_items": ready_items["waiting_retries"],
		"errors": errors,
	}


def process_open_call_queues() -> dict:
	results = []
	for row in frappe.get_all(
		CALL_QUEUE_DOCTYPE,
		filters={"enabled": 1, "status": "Open"},
		fields=["name"],
		order_by="priority asc, modified asc",
	):
		results.append(process_call_queue(row.name))
	return {"queues": results}


@frappe.whitelist()
def create_encounter_queue(
	patient_encounter: str | None = None,
	call_queue: str | None = None,
	priority: str | None = None,
	source_system: str | None = None,
	external_queue_id: str | None = None,
	customer_phone: str | None = None,
	order_id: str | None = None,
	payload_json: str | dict | None = None,
	notes: str | None = None,
	submit_now: int | str | None = None,
):
	request_payload = {}
	try:
		request_json = frappe.request.get_json(silent=True) if getattr(frappe, "request", None) else None
	except Exception:
		request_json = None
	if isinstance(request_json, dict):
		request_payload.update(request_json)
	if getattr(frappe.local, "form_dict", None):
		request_payload.update({k: v for k, v in frappe.local.form_dict.items() if k not in {"cmd", "data"}})

	patient_encounter = patient_encounter or request_payload.get("patient_encounter")
	call_queue = call_queue or request_payload.get("call_queue")
	priority = priority or request_payload.get("priority")
	source_system = source_system or request_payload.get("source_system") or "n8n"
	external_queue_id = external_queue_id or request_payload.get("external_queue_id")
	customer_phone = customer_phone or request_payload.get("customer_phone")
	order_id = order_id or request_payload.get("order_id")
	notes = notes or request_payload.get("notes")
	submit_now = cint(submit_now if submit_now is not None else request_payload.get("submit_now") or 0)
	payload_json = payload_json or request_payload.get("payload_json") or request_json or None

	if not patient_encounter:
		frappe.throw("patient_encounter is required")

	call_queue = call_queue or get_default_call_queue()
	if not call_queue:
		frappe.throw("No open Call Queue found for Voice AI")

	remote_config = get_call_queue_remote_config(call_queue)
	context = {}
	if not remote_config.get("remote_access"):
		encounter_doc = frappe.get_doc("Patient Encounter", patient_encounter)
		context = get_patient_context(encounter_doc)

	existing_name = get_existing_open_queue(patient_encounter)
	created = not bool(existing_name)
	reused = bool(existing_name)
	queue_doc = frappe.get_doc(QUEUE_DOCTYPE, existing_name) if existing_name else frappe.new_doc(QUEUE_DOCTYPE)

	queue_doc.call_queue = call_queue
	queue_doc.patient_encounter = patient_encounter
	queue_doc.patient = context.get("patient") or queue_doc.get("patient")
	queue_doc.patient_name = context.get("patient_name") or queue_doc.get("patient_name")
	queue_doc.customer = context.get("customer") or queue_doc.get("customer")
	queue_doc.customer_name = context.get("customer_name") or queue_doc.get("customer_name")
	queue_doc.customer_phone = normalize_phone_number(customer_phone or context.get("customer_phone") or queue_doc.get("customer_phone"))
	queue_doc.source_system = source_system
	queue_doc.external_queue_id = external_queue_id or queue_doc.external_queue_id
	queue_doc.order_id = order_id or queue_doc.order_id
	if priority:
		queue_doc.priority = priority
	if not queue_doc.queue_status:
		queue_doc.queue_status = "Pending"
	if not queue_doc.telephony_status:
		queue_doc.telephony_status = "queued"

	payload_doc = _json_payload_from_string(payload_json)
	if payload_doc is not None:
		queue_doc.payload_json = json.dumps(payload_doc, default=str)
	_append_api_note(queue_doc, notes)

	from voice_ai.voice_ai.assignment import assign_worker_to_queue_doc

	assign_worker_to_queue_doc(queue_doc)
	queue_doc.flags.ignore_permissions = True
	queue_doc.save(ignore_permissions=True)
	frappe.db.commit()

	if submit_now:
		return submit_encounter_queue(queue_doc.name)

	return build_queue_response(queue_doc, created=created, reused=reused)


@frappe.whitelist()
def process_voice_ai_queues():
	return process_open_call_queues()
