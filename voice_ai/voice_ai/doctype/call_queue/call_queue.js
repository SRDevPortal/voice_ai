frappe.ui.form.on("Call Queue", {
	onload_post_render(frm) {
		configure_remote_access_fields(frm);
	},
	refresh(frm) {
		configure_remote_access_fields(frm);
	},
	onload(frm) {
		configure_remote_access_fields(frm);
	},
});

function configure_remote_access_fields(frm) {
	frm._remote_access_autocomplete_token ||= frappe.utils.get_random(10);
	disable_credential_password_checks(frm);
	disable_remote_access_autofill(frm);
	setTimeout(() => disable_remote_access_autofill(frm), 300);
}

function disable_remote_access_autofill(frm) {
	["remote_site_url", "api_key", "api_secret"].forEach((fieldname) => {
		const field = frm.fields_dict[fieldname];
		if (!field?.$input?.length) {
			return;
		}

		const token = `${frm._remote_access_autocomplete_token}_${fieldname}`;
		field.$input.attr({
			name: `remote_access_${token}`,
			autocomplete: `section-${token} new-password`,
			autocorrect: "off",
			autocapitalize: "off",
			spellcheck: "false",
			"data-lpignore": "true",
			"data-1p-ignore": "true",
			"data-form-type": "other",
		});
	});
}

function disable_credential_password_checks(frm) {
	["api_key", "api_secret"].forEach((fieldname) => {
		const field = frm.fields_dict[fieldname];
		if (!field || typeof field.disable_password_checks !== "function") {
			return;
		}

		field.disable_password_checks();
		field.indicator?.addClass("hidden");
		field.message?.addClass("hidden");
	});
}
