# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "l10n.in.ewaybill.mixin"]

    l10n_in_ewaybill_transaction_ids = fields.One2many(
        "l10n.in.ewaybill.transaction", "move_id", "Ewaybill transaction"
    )

    # just adding depends
    @api.depends("l10n_in_ewaybill_transaction_ids")
    def _compute_l10n_in_ewaybill_details(self):
        return super()._compute_l10n_in_ewaybill_details()

    def _get_ewaybill_transaction_domain(self):
        domain = super()._get_ewaybill_transaction_domain()
        domain += [("move_id", "=", self.id)]
        return domain

    def _generate_ewaybill_transaction(self, values):
        values.update({"move_id": self.id})
        return super()._generate_ewaybill_transaction(values)

    def _prepare_validate_ewaybill_message(self):
        message = super()._prepare_validate_ewaybill_message()
        for move in self.invoice_line_ids.filtered(lambda l: not l.is_rounding_line):
            if move.product_id and not move.product_id.l10n_in_hsn_code:
                message += "\n- Product(%s) required HSN Code" % (move.product_id.name)
        return message
