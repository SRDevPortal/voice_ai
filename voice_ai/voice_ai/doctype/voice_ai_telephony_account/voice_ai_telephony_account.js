frappe.ui.form.on('Voice AI Telephony Account', {
    refresh: function(frm) {
        // Fetch active physical workers from the server
        frappe.call({
            method: "voice_ai.voice_ai.processor.get_active_background_queues",
            callback: function(r) {
                if (r.message) {
                    // Set the options for the background_queue_name field
                    frm.set_df_property('background_queue_name', 'options', r.message);
                }
            }
        });
    }
});
