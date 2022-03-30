# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "eWayBill for India (stock)",
    "summary": """
        Create an eWayBill to transer the goods in India""",
    "description": """
        This module Create an eWayBill from stock picking
    """,
    "author": "Odoo",
    "website": "http://www.odoo.com",
    "category": "Accounting/Accounting",
    "version": "1.0",
    "depends": ["stock", "l10n_in_ewaybill"],
    "data": [
        "data/ewaybill_generate_stock_json.xml",
        "data/ewaybill_extend_json.xml",
        "data/ewaybill_update_part_b_stock_json.xml",
        "views/stock_picking_view.xml",
        "views/ewaybill_transaction_views.xml",
        "report/report_deliveryslip.xml",
        "report/report_stockpicking_operations.xml",
    ],
    "installable": True,
    "auto_install": True,
    "license": "OEEL-1",
}
