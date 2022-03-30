# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Indian - Accounting extend Sale, Stock",
    "version": "1.0",
    "description": """
Indian - Accounting extend Sale, Stock
======================================

If invoice is create from sale,
then set dispatch address from warehouse address if available.

if we found more then one warehouse for single invoice then we don't set dispatch address.
So in this case select dispatch address manually.
    """,
    "category": "Accounting/Accounting",
    "depends": ["l10n_in_extend", "sale_stock"],
    "data": [
        "wizard/sale_make_invoice_advance_views.xml",
    ],
    "installable": True,
    "auto_install": True,
    "license": "OEEL-1",
}
