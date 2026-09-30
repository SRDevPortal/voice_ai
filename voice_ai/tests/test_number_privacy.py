import unittest
from unittest.mock import patch
from voice_ai.number_privacy import project_response

class NumberPrivacyTests(unittest.TestCase):
    def test_restricted_response_does_not_change_provider_input(self):
        raw = {"customer_number": "9876501234", "customer_phone": "9876501234",
               "recording_url": "https://example.invalid/audio", "transcript_text": "9876501234",
               "ai_summary": "Call 9876501234", "queue_status": "Pending",
               "session_id": "queue_9876501234", "message": "Number 9876501234 failed"}
        with patch('voice_ai.number_privacy.restricted', return_value=True):
            result = project_response(raw)
        self.assertNotIn('9876501234', str(result))
        self.assertEqual(result['queue_status'], 'Pending')
        self.assertEqual(raw['customer_phone'], '9876501234')
        self.assertTrue(raw['recording_url'])

    def test_full_visibility_preserves_response(self):
        raw = [{"customer_number": "9876501234", "recording_url": "audio"}]
        with patch('voice_ai.number_privacy.restricted', return_value=False):
            self.assertEqual(project_response(raw), raw)

    def test_queue_create_denied_before_assignment_or_provider(self):
        import frappe
        from voice_ai.voice_ai import processor
        with patch.object(processor, 'frappe') as fake, patch.object(processor, 'submit_encounter_queue') as send:
            fake.request.get_json.return_value = {}
            fake.local.form_dict = {}
            fake.db.exists.return_value = True
            fake.get_doc.return_value.check_permission.side_effect = frappe.PermissionError
            with self.assertRaises(frappe.PermissionError):
                processor.create_encounter_queue.__wrapped__(call_queue='queue',submit_now=1)
            fake.db.commit.assert_not_called()
            send.assert_not_called()

    def test_queue_callback_denied_before_logging_or_updates(self):
        import frappe
        from voice_ai.voice_ai import processor
        with patch.object(processor,'frappe') as fake:
            fake.has_permission.side_effect=frappe.PermissionError
            with self.assertRaises(frappe.PermissionError):
                processor.update_encounter_status.__wrapped__('queue',telephony_status='completed')
            fake.log_error.assert_not_called()
            fake.db.set_value.assert_not_called()

    def test_internal_queue_response_remains_raw(self):
        import frappe
        from voice_ai.voice_ai.processor import build_queue_response
        doc=frappe._dict(name='queue',customer_phone='9876501234')
        self.assertEqual(build_queue_response(doc)['customer_phone'],'9876501234')

    def test_raw_diagnostics_denied_before_query_for_restricted_manager(self):
        import frappe
        from voice_ai.voice_ai import processor
        for name in ('read_logs', 'analyze_webhook_formats'):
            with self.subTest(endpoint=name), patch.object(processor, 'frappe') as fake, patch('voice_ai.number_privacy.restricted', return_value=True):
                with self.assertRaises(frappe.PermissionError):
                    getattr(processor, name).__wrapped__()
                fake.only_for.assert_called_once_with('System Manager')
                fake.get_all.assert_not_called()

    def test_raw_diagnostics_full_visibility_keeps_manager_check(self):
        from voice_ai.voice_ai import processor
        for name in ('read_logs', 'analyze_webhook_formats'):
            with self.subTest(endpoint=name), patch.object(processor, 'frappe') as fake, patch('voice_ai.number_privacy.restricted', return_value=False):
                fake.get_all.return_value = [{'error': 'synthetic diagnostic'}]
                self.assertEqual(getattr(processor, name).__wrapped__(), fake.get_all.return_value)
                fake.only_for.assert_called_once_with('System Manager')
