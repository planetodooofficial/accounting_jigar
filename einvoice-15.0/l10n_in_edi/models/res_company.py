# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_in_edi_username = fields.Char("Username")
    l10n_in_edi_password = fields.Char("Password", groups="base.group_system")
