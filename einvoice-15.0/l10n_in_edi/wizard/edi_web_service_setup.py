# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class L10nInEdiWebServiceSetupWizard(models.TransientModel):
    _name = "l10n.in.edi.web.service.setup.wizard"
    _description = "Indian eInvoice Service Setup"

    def _get_default_company(self):
        company = self.env.company
        active_model = self._context.get("active_model", False)
        model_id = self._context.get("active_id", False)
        if active_model_id and model_id:
            active_model_id = self.env[active_model].browse([model_id])
            if "company_id" in active_model_id:
                company = active_model_id.company_id
        return company

    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=_get_default_company
    )
    l10n_in_edi_username = fields.Char(
        related="company_id.l10n_in_edi_username", readonly=False, required=True
    )
    l10n_in_edi_password = fields.Char(
        related="company_id.l10n_in_edi_password", readonly=False, required=True
    )

    def setup_web_service(self):
        service = self.env["l10n.in.edi.web.service"].get_service(
            self.company_id, create_if_not_found=True
        )
        response = service.setup()
