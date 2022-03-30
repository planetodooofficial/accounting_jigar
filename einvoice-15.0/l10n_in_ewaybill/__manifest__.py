# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "eWayBill for India",
    "summary": """
        Create an eWayBill to transer the goods in India""",
    "description": """
Indian - E-Waybill
====================
To Create E-Waybill through API.
We use "Tera Software Limited" as GSP

Step 1: First you need to create api username and password in E-waybill portal.
Step 2: Swich to company related to that GST nubmer
Step 3: Set that username and password in Odoo (Goto: Settings -> General Settings -> Contacts section or find "E-waybill" in search bar)
Step 4: Repeat step 1,2,3 for all GSTIN you have in odoo. If you have multi-compnay with same GST nubmer then perform step 1 for first company only.
    """,
    "author": "Odoo",
    "website": "http://www.odoo.com",
    "category": "Accounting/Accounting",
    "version": "1.1",
    "depends": ["l10n_in_extend"],
    "data": [
        "security/ir.model.access.csv",
        "data/ewaybill_type_data.xml",
        "data/ewaybill_generate_json.xml",
        "data/ewaybill_cancel_json.xml",
        "data/ewaybill_update_part_b_json.xml",
        "data/ewaybill_extend_json.xml",
        "views/ewaybill_transaction_views.xml",
        "views/account_move_views.xml",
        "wizard/generate_token_wizard_views.xml",
        "wizard/cancel_ewaywill_wizard_views.xml",
        "wizard/ewaybill_update_part_b_wizard_views.xml",
        "wizard/extend_ewaybill_wizard_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "OEEL-1",
}
