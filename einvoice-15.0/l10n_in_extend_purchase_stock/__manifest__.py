# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Indian - Accounting extend Purchase, stock",
    "version": "1.0",
    "description": """
Indian - Accounting extend Purchase, Stock
==========================================

If bill is create from purchase,
then set dispatch address from warehouse address if available.

if we found more then one warehouse for single bill then we don't set dispatch address.
So in this case select dispatch address manually.
    """,
    "category": "Accounting/Accounting",
    "depends": ["l10n_in_extend", "purchase_stock"],
    "data": [],
    "installable": True,
    "auto_install": True,
    "license": "OEEL-1",
}
