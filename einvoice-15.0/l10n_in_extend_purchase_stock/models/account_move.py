# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.company_id.country_id.code != "IN" and not res.is_purchase_document():
            return res
        company_shipping_id = res.mapped(
            "invoice_line_ids.purchase_line_id.move_ids.warehouse_id.partner_id"
        )
        if not res.company_shipping_id and len(company_shipping_id) == 1:
            res.company_shipping_id = company_shipping_id
        return res
