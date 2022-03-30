# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_ewaybill_invoice_partner(self):
        res = super()._get_ewaybill_invoice_partner()
        if self.move_lines.purchase_line_id:
            purchase_order = self.mapped("move_lines.purchase_line_id.order_id")
            partner_ids = purchase_order.mapped("invoice_ids.partner_id")
            if partner_ids:
                return partner_ids[0]
            else:
                partner_ids = purchase_order.mapped("partner_id")
                # get invoice address from partner of purchase order
                if partner_ids:
                    invoice_partner_id = partner_ids[0].address_get(["invoice"])[
                        "invoice"
                    ]
                    return self.env['res.partner'].browse([invoice_partner_id])
        return res
