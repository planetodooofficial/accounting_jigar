# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    l10n_in_ewaybill_tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        compute="_compute_l10n_in_ewaybill_tax_ids",
        store=True,
        readonly=False,
        copy=False,
    )
    l10n_in_ewaybill_price_taxexcl = fields.Float(
        "Price Tax excl",
        compute="_compute_l10n_in_ewaybill_unit_price",
        store=True,
        readonly=False,
        copy=False,
    )

    @api.depends("product_id", "partner_id")
    def _compute_l10n_in_ewaybill_tax_ids(self):
        FiscalPosition = self.env["account.fiscal.position"]
        for move_line in self:
            taxe_ids = False
            if move_line.product_id:
                fiscal_position_id = FiscalPosition.get_fiscal_position(
                    move_line.partner_id.id
                )
                taxe_ids = move_line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == move_line.company_id
                )
                taxe_ids = fiscal_position_id.map_tax(taxe_ids._origin)
            move_line.l10n_in_ewaybill_tax_ids = taxe_ids

    @api.depends(
        "product_uom", "product_id", "partner_id"
    )
    def _compute_l10n_in_ewaybill_unit_price(self):
        for move_line in self:
            price_taxexcl = 0.00
            partner = move_line.partner_id
            if move_line.product_id:
                price = move_line.product_id.with_context(
                    pricelist=partner.property_product_pricelist.id,
                    partner=partner.id,
                    uom=move_line.product_uom.id,
                    date=move_line.picking_id.date_done,
                ).price
                price_taxexcl = self.env["account.tax"]._fix_tax_included_price_company(
                    price,
                    move_line.product_id.taxes_id,
                    move_line.l10n_in_ewaybill_tax_ids,
                    move_line.company_id,
                )
            move_line.l10n_in_ewaybill_price_taxexcl = price_taxexcl
