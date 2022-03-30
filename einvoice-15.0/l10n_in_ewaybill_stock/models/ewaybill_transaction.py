# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

TEMPLATES = {
    "generate": "l10n_in_ewaybill_stock.l10n_in_ewaybill_generate_stock_json",
    "update_partb": "l10n_in_ewaybill_stock.l10n_in_ewaybill_update_part_b_stock_json",
    "extend_date": "l10n_in_ewaybill_stock.l10n_in_ewaybill_extend_stock_json",
}

class EwayBill(models.Model):
    _inherit = "l10n.in.ewaybill.transaction"

    picking_id = fields.Many2one("stock.picking", string="Stock Picking")

    @api.depends("picking_id", "move_id")
    def _compute_request_json(self):
        return super()._compute_request_json()

    def _get_last_generate_request(self):
        if self.picking_id:
            last_generate_request = self.search(
                [
                    ("picking_id", "=", self.picking_id.id),
                    ("request_type", "=", "generate"),
                ],
                limit=1,
            )
            return last_generate_request
        return super()._get_last_generate_request()

    def _prepare_compute_request_json_template_values(self):
        values = super()._prepare_compute_request_json_template_values()
        if self.picking_id:
            values.update(
                {
                    "picking": self.picking_id,
                    "tax_details": self.picking_id._get_ewaybill_line_tax_details(),
                }
            )
        return values

    def _get_ewaybill_templates(self):
        self.ensure_one()
        if self.picking_id and TEMPLATES.get(self.request_type, False):
            return TEMPLATES[self.request_type]
        return super()._get_ewaybill_templates()

    def _get_source_document(self):
        source_document = super()._get_source_document()
        if self.picking_id:
            source_document += self.picking_id.name
        return source_document
