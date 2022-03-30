# -*- coding: utf-8 -*-

from odoo import api
from odoo import SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("CREATE TABLE l10n_in_einvoice_transaction_copy AS TABLE l10n_in_einvoice_transaction")
