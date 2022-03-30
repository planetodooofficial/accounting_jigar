# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    company_shipping_id = fields.Many2one(
        "res.partner",
        string="Dispatch Address",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Dispatch/Delivery address for current invoice/bill",
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # it's depricate after V15 so don't use still here becosue support old invoices
    base_line_ref = fields.Char(
        "Matching Ref",
        help="Technical field to map invoice base line with its tax lines.",
    )
