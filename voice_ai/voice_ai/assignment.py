"""Queue assignment helpers for Voice AI."""

from __future__ import annotations

import frappe


ACTIVE_ASSIGNMENT_STATUSES = {"Assigned", "Picked", "In Progress", "Retry Scheduled"}
ACTIVE_WORKER_STATUSES = {"idle", "ready", "busy"}


def get_worker_active_load(worker_name: str) -> int:
	return frappe.db.count(
		"Voice AI Encounter Queue",
		{
			"assigned_worker": worker_name,
			"queue_status": ["in", list(ACTIVE_ASSIGNMENT_STATUSES)],
		},
	)


def refresh_worker_active_load(worker_name: str) -> int:
	load = get_worker_active_load(worker_name)
	if frappe.db.exists("Voice AI Worker", worker_name):
		frappe.db.set_value("Voice AI Worker", worker_name, "current_active_calls", load, update_modified=False)
	return load


def get_eligible_workers(call_queue: str) -> list[dict]:
	if not call_queue:
		return []

	queue_settings = frappe.db.get_value(
		"Call Queue",
		call_queue,
		["enabled", "status", "auto_assign_workers"],
		as_dict=True,
	)
	if not queue_settings or not queue_settings.enabled or queue_settings.status != "Open":
		return []
	if not int(queue_settings.auto_assign_workers or 0):
		return []

	workers = frappe.get_all(
		"Voice AI Worker",
		filters={
			"enabled": 1,
			"auto_assign_enabled": 1,
			"status": ["in", list(ACTIVE_WORKER_STATUSES)],
		},
		fields=[
			"name",
			"worker_name",
			"status",
			"max_concurrent_calls",
			"assignment_priority",
			"default_agent_id",
			"default_phone_number_id",
		],
		order_by="assignment_priority asc, modified asc",
	)

	eligible = []
	for worker in workers:
		allowed_queue = frappe.db.exists(
			"Voice AI Worker Queue",
			{"parent": worker.name, "parenttype": "Voice AI Worker", "call_queue": call_queue},
		)
		if not allowed_queue:
			continue

		current_load = get_worker_active_load(worker.name)
		max_calls = int(worker.max_concurrent_calls or 1)
		if current_load >= max_calls:
			continue

		worker["current_load"] = current_load
		eligible.append(worker)

	return sorted(
		eligible,
		key=lambda row: (
			int(row.get("current_load") or 0),
			int(row.get("assignment_priority") or 100),
			(row.get("worker_name") or row.get("name") or ""),
		),
	)


def assign_worker_to_queue_doc(queue_doc) -> str | None:
	if not queue_doc.get("call_queue"):
		return None
	if queue_doc.get("assigned_worker"):
		refresh_worker_active_load(queue_doc.assigned_worker)
		return queue_doc.assigned_worker

	eligible = get_eligible_workers(queue_doc.call_queue)
	if not eligible:
		return None

	best_worker = eligible[0]
	queue_doc.assigned_worker = best_worker.name
	queue_doc.assigned_agent = (
		best_worker.get("default_agent_id")
		or queue_doc.get("assigned_agent")
		or frappe.db.get_value("Call Queue", queue_doc.call_queue, "default_agent_id")
	)
	if (queue_doc.get("queue_status") or "Pending") == "Pending":
		queue_doc.queue_status = "Assigned"
	if not queue_doc.get("assigned_at"):
		queue_doc.assigned_at = frappe.utils.now_datetime()
	return queue_doc.assigned_worker
