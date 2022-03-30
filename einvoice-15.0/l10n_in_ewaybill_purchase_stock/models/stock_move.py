# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends(
        "product_id",
        "partner_id",
        "purchase_line_id",
        "purchase_line_id.taxes_id",
    )
    def _compute_l10n_in_ewaybill_tax_ids(self):
        super()._compute_l10n_in_ewaybill_tax_ids()
        for move_line in self:
            if move_line.purchase_line_id:
                move_line.l10n_in_ewaybill_tax_ids = move_line.purchase_line_id.taxes_id

    @api.depends(
        "product_uom",
        "product_id",
        "partner_id",
        "l10n_in_ewaybill_tax_ids",
        "purchase_line_id",
        "purchase_line_id.price_subtotal",
        "purchase_line_id.product_qty",
        "purchase_line_id.order_id.currency_rate",
    )
    def _compute_l10n_in_ewaybill_unit_price(self):
        super()._compute_l10n_in_ewaybill_unit_price()
        for move_line in self:
            purchase_line = move_line.purchase_line_id
            if purchase_line:
                move_line.l10n_in_ewaybill_price_taxexcl = (
                    purchase_line.price_subtotal / purchase_line.product_qty
                ) * purchase_line.order_id.currency_rate
