# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class WaybillServiceSetupWizard(models.TransientModel):
    _name = "l10n.in.ewaybill.service.setup.wizard"
    _description = "ewaybill service setup wizard"

    def _get_default_company(self):
        company = self.env.company
        active_model = self._context.get("active_model", False)
        model_id = self._context.get("active_id", False)
        if active_model and model_id:
            active_model_id = self.env[active_model].browse([model_id])
            if "company_id" in active_model_id:
                company = active_model_id.company_id
        return company

    company_id = fields.Many2one(
        "res.company", string="Company", default=_get_default_company
    )
    gstn_username = fields.Char("Username", required=True)
    gstn_password = fields.Char("Password", required=True)
    save_password = fields.Boolean("Save Password")

    def register_service(self):
        EwaybillService = self.env["l10n.in.ewaybill.service"]
        service_id = EwaybillService.search(
            [
                ("company_id", "=", self.company_id.id),
                ("gstin", "=", self.company_id.vat),
                ("gstn_username", "=", self.gstn_username),
            ]
        )
        if not service_id:
            service_id = EwaybillService.create(
                {
                    "company_id": self.company_id.id,
                    "gstn_username": self.gstn_username,
                    "gstin": self.company_id.vat,
                }
            )
        if self.save_password:
            service_id.gstn_password = self.gstn_password
        service_id.setup(self.gstn_password)
