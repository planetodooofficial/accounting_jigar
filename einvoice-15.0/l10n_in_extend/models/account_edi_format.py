# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import json
import html2text

from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import plaintext2html


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    @api.model
    def _l10n_in_filter_to_apply(self, tax_values):
        if tax_values["base_line_id"].is_rounding_line:
            return False
        return True

    @api.model
    def _l10n_in_grouping_key_generator(self, tax_values):
        base_line = tax_values["base_line_id"]
        tax_line = tax_values["tax_line_id"]
        return {
            "tax": tax_values["tax_id"],
            "base_product_id": base_line.product_id,
            "tax_product_id": tax_line.product_id,
            "base_product_uom_id": base_line.product_uom_id,
            "tax_product_uom_id": tax_line.product_uom_id,
        }

    @api.model
    def _l10n_in_prepare_edi_tax_details(self, invoice, in_foreign=False):
        gst_tag_ids = {
            "igst": self.env.ref("l10n_in.tax_report_line_igst").tag_ids,
            "sgst": self.env.ref("l10n_in.tax_report_line_sgst").tag_ids,
            "cgst": self.env.ref("l10n_in.tax_report_line_cgst").tag_ids,
        }
        all_gst_tag_ids = sum(gst_tag_ids.values(), self.env["account.account.tag"])
        cess_tag_ids = {
            "cess": self.env.ref("l10n_in.tax_report_line_cess").tag_ids,
        }
        state_cess_tag_ids = {
            "state_cess": self.env.ref(
                "l10n_in_extend.tax_report_line_state_cess"
            ).tag_ids,
        }

        invoice_tax_values = invoice._prepare_edi_tax_details(
            filter_to_apply=self._l10n_in_filter_to_apply,
            grouping_key_generator=self._l10n_in_grouping_key_generator,
        )
        is_reverse_charge = False
        for line in invoice.invoice_line_ids:
            invoice_tax_values["invoice_line_tax_details"].setdefault(line, {})
            invoice_line_tax_details = invoice_tax_values[
                "invoice_line_tax_details"
            ].get(line)
            tax_ids = line.tax_ids.flatten_taxes_hierarchy()
            extra_tax_details = {
                "gst_rate": sum(
                    tax.amount
                    for tax in tax_ids
                    if any(
                        tag
                        for tag in tax.invoice_repartition_line_ids.tag_ids
                        if tag in all_gst_tag_ids
                    )
                ),
                "cess_rate": sum(
                    tax.amount
                    for tax in tax_ids
                    if tax.amount_type == "percent"
                    and any(
                        tag
                        for tag in tax.invoice_repartition_line_ids.tag_ids
                        if tag in cess_tag_ids["cess"]
                    )
                ),
                "state_cess_rate": sum(
                    tax.amount
                    for tax in tax_ids
                    if tax.amount_type == "percent"
                    and any(
                        tag
                        for tag in tax.invoice_repartition_line_ids.tag_ids
                        if tag in state_cess_tag_ids["state_cess"]
                    )
                ),
                "other": 0.00,
            }
            for group_key, tax_details in invoice_line_tax_details.get(
                "tax_details", {}
            ).items():
                for tax_detail in tax_details["group_tax_details"]:
                    is_other_tax = True
                    tax_line_id = tax_detail["tax_line_id"]
                    if (
                        not is_reverse_charge
                        and tax_detail["tax_id"].l10n_in_reverse_charge
                    ):
                        is_reverse_charge = True
                    for tax_key, tag_ids in {
                        **gst_tag_ids,
                        **cess_tag_ids,
                        **state_cess_tag_ids,
                    }.items():
                        # non_advol is only aplicabe in cess
                        if (
                            tax_detail["tax_id"].amount_type != "percent"
                            and "cess" in tax_key
                        ):
                            tax_key = tax_key + "_non_advol"
                        if any(
                            tag for tag in tax_line_id.tax_tag_ids if tag in tag_ids
                        ):
                            extra_tax_details.setdefault(tax_key, 0.00)
                            extra_tax_details[tax_key] += tax_details[
                                in_foreign and "tax_amount_currency" or 'tax_amount'
                            ]
                            is_other_tax = False
                            continue
                    if (
                        is_other_tax
                        and tax_line_id.tax_repartition_line_id.factor_percent > 0.00
                    ):
                        extra_tax_details["other"] += tax_details[in_foreign and "tax_amount_currency" or 'tax_amount']
            invoice_line_tax_details.update(extra_tax_details)
        return {
            "move": invoice,
            "is_reverse_charge": is_reverse_charge,
            "invoice_tax_details": invoice_tax_values,
        }
