# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def l10n_in_edi_setup(self):
        view_id = self.env.ref("l10n_in_edi.l10n_in_edi_web_service_setup_wizard").id
        context = self.env.context.copy()
        context.update({"default_company_id": self.company_id.id})
        return {
            "name": _("Setup Indian E-invoice"),
            "view_mode": "form",
            "views": [[view_id, "form"]],
            "res_model": "l10n.in.edi.web.service.setup.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": context,
        }
