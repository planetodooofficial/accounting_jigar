# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "l10n.in.ewaybill.mixin"]

    l10n_in_ewaybill_transaction_ids = fields.One2many(
        "l10n.in.ewaybill.transaction", "picking_id", "Ewaybill transaction"
    )

    # just adding depends
    @api.depends("l10n_in_ewaybill_transaction_ids")
    def _compute_l10n_in_ewaybill_details(self):
        return super()._compute_l10n_in_ewaybill_details()

    def _get_ewaybill_transaction_domain(self):
        domain = super()._get_ewaybill_transaction_domain()
        domain += [("picking_id", "=", self.id)]
        return domain

    def _generate_ewaybill_transaction(self, values):
        values.update({"picking_id": self.id})
        return self.env["l10n.in.ewaybill.transaction"].create(values)

    # TO BE OVERWRITTEN in sale and purchase
    def _get_ewaybill_invoice_partner(self):
        self.ensure_one()
        return False

    def _prepare_validate_ewaybill_message(self):
        message = super()._prepare_validate_ewaybill_message()
        for move in self.move_ids_without_package:
            if move.product_id and not move.product_id.l10n_in_hsn_code:
                message += "\n- Product(%s) required HSN Code" % (move.product_id.name)
        return message


    def _get_ewaybill_line_tax_details(self):
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
        picking_tax_details = {}
        for picking in self:
            is_reverse_charge = False
            line_tax_details = {}
            for move_line in picking.move_ids_without_package:
                line_tax_details.setdefault(move_line, {})
                tax_ids = move_line.l10n_in_ewaybill_tax_ids.flatten_taxes_hierarchy()
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
                taxs_compute = move_line.l10n_in_ewaybill_tax_ids.compute_all(
                    price_unit=move_line.l10n_in_ewaybill_price_taxexcl,
                    quantity=move_line.quantity_done,
                    product=move_line.product_id,
                    handle_price_include=False,
                )
                for tax in taxs_compute["taxes"]:
                    is_other_tax = True
                    # tax_line_id = tax_detail['tax_line_id']
                    tax_id = self.env["account.tax"].browse(tax["id"])
                    tax_repartition_line_id = self.env[
                        "account.tax.repartition.line"
                    ].browse(tax["tax_repartition_line_id"])
                    if not is_reverse_charge and tax_id.l10n_in_reverse_charge:
                        is_reverse_charge = True
                    for tax_key, tag_ids in {
                        **gst_tag_ids,
                        **cess_tag_ids,
                        **state_cess_tag_ids,
                    }.items():
                        # non_advol is only aplicabe in cess
                        if tax_id.amount_type != "percent" and "cess" in tax_key:
                            tax_key = tax_key + "_non_advol"
                        if any(tag for tag in tax["tag_ids"] if tag in tag_ids.ids):
                            extra_tax_details.setdefault(tax_key, 0.00)
                            extra_tax_details[tax_key] += tax["amount"]
                            is_other_tax = False
                            continue
                    if is_other_tax and tax_repartition_line_id.factor_percent > 0.00:
                        extra_tax_details["other"] += tax_details["tax_amount_currency"]
                line_tax_details[move_line].update(
                    {**taxs_compute, **extra_tax_details}
                )
            picking_tax_details[picking] = {
                "line_tax_details": line_tax_details,
                "is_reverse_charge": is_reverse_charge,
            }
        return picking_tax_details
