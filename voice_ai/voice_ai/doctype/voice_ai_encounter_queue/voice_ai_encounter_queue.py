from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

NON_SUBMITTED_STATUSES = {"Pending", "Assigned", "Picked", "In Progress", "Retry Scheduled"}


class VoiceAIEncounterQueue(Document):
	def before_insert(self):
		if not self.session_id:
			self.session_id = f"vs_{uuid4().hex}"
		if not self.created_at:
			self.created_at = now_datetime()

	def validate(self):
		self._validate_call_queue_state()
		self._apply_retry_policy_defaults()
		self._validate_patient_encounter_uniqueness()
		self._apply_status_timestamps()

	def _validate_call_queue_state(self):
		if not self.call_queue:
			return
		queue_state = frappe.db.get_value("Call Queue", self.call_queue, ["enabled", "status"], as_dict=True)
		if not queue_state:
			return
		if not queue_state.enabled:
			frappe.throw(f"Call Queue {self.call_queue} is disabled")
		if queue_state.status == "Closed":
			frappe.throw(f"Call Queue {self.call_queue} is closed")

	def _apply_retry_policy_defaults(self):
		if not self.retry_policy and self.call_queue:
			self.retry_policy = frappe.db.get_value("Call Queue", self.call_queue, "retry_policy")
		if self.retry_policy and not self.max_attempts:
			self.max_attempts = (
				frappe.db.get_value("Voice AI Retry Policy", self.retry_policy, "max_attempts")
				or self.max_attempts
				or 0
			)

	def _validate_patient_encounter_uniqueness(self):
		if not self.patient_encounter:
			return
		existing = frappe.get_all(
			"Voice AI Encounter Queue",
			filters={
				"patient_encounter": self.patient_encounter,
				"name": ["!=", self.name or ""],
				"queue_status": ["in", list(NON_SUBMITTED_STATUSES)],
			},
			fields=["name", "queue_status", "call_queue"],
			limit=1,
		)
		if existing:
			row = existing[0]
			frappe.throw(
				f"Encounter Queue {row.name} already exists for Patient Encounter {self.patient_encounter} "
				f"with status {row.queue_status} in queue {row.call_queue}. "
				"Only one non-submitted queue item is allowed at a time."
			)

	def _apply_status_timestamps(self):
		current_status = self.queue_status or "Pending"
		now = now_datetime()
		self.last_status_at = now

		if current_status == "Assigned" and not self.assigned_at:
			self.assigned_at = now
		elif current_status == "Picked" and not self.picked_at:
			self.picked_at = now
		elif current_status == "In Progress" and not self.started_at:
			self.started_at = now
		elif current_status == "Submitted" and not self.submitted_at:
			self.submitted_at = now
		elif current_status in {"Completed", "Failed", "Escalated", "Closed"} and not self.ended_at:
			self.ended_at = now
