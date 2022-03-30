# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class AccountEdiDocument(models.Model):
    _inherit = "account.edi.document"

    state = fields.Selection(selection_add=[("to_confirm", "To confirm")])
