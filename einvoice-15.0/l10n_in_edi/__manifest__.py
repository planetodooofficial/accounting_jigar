# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": """Indian - E-invoicing""",
    "version": "1.03.00",
    "category": "Accounting/Localizations",
    "depends": [
        "account_edi",
        "l10n_in",
        "iap",
        "l10n_in_extend",
        "account_edi_double_check",
    ],
    "description": """
Indian - E-invoicing
====================
To submit invoicing through API to government.
We use "Tera Software Limited" as GSP

Step 1: First you need to create api username and password in E-invoice portal.
Step 2: Swich to company related to that GST nubmer
Step 3: Set that username and password in Odoo (Goto: Settings -> General Settings -> Contacts section or find "E-invoice" in search bar)
Step 4: Repeat step 1,2,3 for all GSTIN you have in odoo. If you have multi-compnay with same GST nubmer then perform step 1 for first company only.

For creation of api username and password plz ref this document: <https://service.odoo.co.in/einvoice_create_api_user>
    """,
    "data": [
        "security/ir.model.access.csv",
        "data/account_edi_data.xml",
        "data/account_invoice_json.xml",
        "wizard/edi_web_service_setup_views.xml",
        "views/res_config_settings_views.xml",
        "views/edi_pdf_report.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    # only aplicabe for taxpayers turnover higher than Rs.50 crore so auto install is False
    "auto_install": False,
    "application": False,
    "license": "OEEL-1",
}
