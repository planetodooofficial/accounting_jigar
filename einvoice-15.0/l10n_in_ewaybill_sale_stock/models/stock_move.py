# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends(
        "product_id", "partner_id", "sale_line_id", "sale_line_id.tax_id"
    )
    def _compute_l10n_in_ewaybill_tax_ids(self):
        super()._compute_l10n_in_ewaybill_tax_ids()
        for move_line in self:
            if move_line.sale_line_id:
                move_line.l10n_in_ewaybill_tax_ids = move_line.sale_line_id.tax_id

    @api.depends(
        "product_uom",
        "product_id",
        "partner_id",
        "sale_line_id",
        "sale_line_id.price_reduce_taxexcl",
        "sale_line_id.order_id.currency_rate",
    )
    def _compute_l10n_in_ewaybill_unit_price(self):
        super()._compute_l10n_in_ewaybill_unit_price()
        for move_line in self:
            if move_line.sale_line_id:
                move_line.l10n_in_ewaybill_price_taxexcl = (
                    move_line.sale_line_id.price_reduce_taxexcl
                    * move_line.sale_line_id.order_id.currency_rate
                )
