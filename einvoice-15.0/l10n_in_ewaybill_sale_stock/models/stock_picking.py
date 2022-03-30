# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_ewaybill_invoice_partner(self):
        res = super()._get_ewaybill_invoice_partner()
        if self.move_lines.sale_line_id:
            partner_ids = self.mapped(
                "move_lines.sale_line_id.order_id.partner_invoice_id"
            ) or self.mapped("move_lines.sale_line_id.order_id.partner_id")
            if partner_ids:
                return partner_ids[0]
        return res
