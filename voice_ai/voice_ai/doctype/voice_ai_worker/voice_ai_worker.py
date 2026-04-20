import frappe
from frappe.model.document import Document

from voice_ai.voice_ai.assignment import refresh_worker_active_load


class VoiceAIWorker(Document):
	def validate(self):
		if not self.worker_name:
			self.worker_name = self.name

	def on_update(self):
		refresh_worker_active_load(self.name)

	@frappe.whitelist()
	def refresh_load(self):
		load = refresh_worker_active_load(self.name)
		self.current_active_calls = load
		return load
