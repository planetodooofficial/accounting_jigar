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

    def _is_enabled_by_default_on_journal(self, journal):
        self.ensure_one()
        if self.code == "in_einvoice_1_03":
            return False
        return super()._is_enabled_by_default_on_journal(journal)

    def _is_required_for_invoice(self, invoice):
        self.ensure_one()
        if self.code == "in_einvoice_1_03":
            return invoice.l10n_in_gst_treatment in (
                "regular",
                "composition",
                "overseas",
                "special_economic_zone",
                "deemed_export",
            )
        return super()._is_required_for_invoice(invoice)

    def _needs_web_services(self):
        self.ensure_one()
        return self.code == "in_einvoice_1_03" and True or super()._needs_web_services()

    def _check_move_configuration(self, move):
        self.ensure_one()
        if self.code == "in_einvoice_1_03":
            self._l10n_in_validate_partner(move.partner_id)
            self._l10n_in_validate_partner(move.company_id.partner_id, is_company=True)
            message = str()
            if not move.name or not re.match("^.{1,16}$", move.name):
                message += "\n- Invoice number should not be more than 16 charactor"
            for line in move.invoice_line_ids:
                if line.product_id:
                    if not line.product_id.l10n_in_hsn_code:
                        message += "\n- HSN code is not set in product %s" % (
                            line.product_id.name
                        )
                    elif not re.match("^[0-9]+$", line.product_id.l10n_in_hsn_code):
                        message += "\n- Invalid HSN Code (%s) in product %s" % (
                            line.product_id.l10n_in_hsn_code,
                            line.product_id.name,
                        )

            if message:
                raise UserError(
                    "Data not valid for the Invoice: %s\n%s" % (move.name, message)
                )
        return super()._check_move_configuration(move)

    def _post_invoice_edi(self, invoices):
        if self.code == "in_einvoice_1_03":
            res = {}
            for invoice in invoices:
                service = self.env["l10n.in.edi.web.service"].get_service(
                    invoice.company_id
                )
                response = False
                try:
                    response = service.generate(self._l10n_in_prepare_json(invoice))
                except UserError as e:
                    if "[2150] Duplicate IRN" in e.data.get("message"):
                        # Get IRN by details in case of IRN is already generated
                        # this happens when timeout from the Government portal but IRN is generated
                        try:
                            response = service.get_irn_by_details(
                                {
                                    "doc_type": invoice.move_type == "out_refund"
                                    and "CRN"
                                    or "INV",
                                    "doc_num": invoice.name,
                                    "doc_date": invoice.invoice_date
                                    and invoice.invoice_date.strftime("%d/%m/%Y")
                                    or False,
                                }
                            )
                        except UserError:
                            pass
                    if not response:
                        res[invoice] = {"success": False, "error": plaintext2html(e)}
                        continue
                except RedirectWarning as e:
                    res[invoice] = {
                        "success": False,
                        "error": plaintext2html(e)
                        + "<button name='90' type='action' class='oe_link' string='config' />",
                    }
                    continue
                json_dump = json.dumps(response.get("data"))
                json_name = "%s_einoivce.json" % (invoice.name.replace("/", "_"))
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": json_name,
                        "raw": json_dump.encode(),
                        "res_model": "account.move",
                        "res_id": invoice.id,
                        "mimetype": "application/json",
                        "description": _(
                            "Indian E-Invoice generated for the %s document.",
                            invoice.name,
                        ),
                    }
                )
                res[invoice] = {"success": True, "attachment": attachment}
            return res
        return super()._post_invoice_edi(invoices)

    def _cancel_invoice_edi(self, invoices):
        if self.code == "in_einvoice_1_03":
            res = {}
            for invoice in invoices:
                service = self.env["l10n.in.edi.web.service"].get_service(
                    invoice.company_id
                )
                l10n_in_send_json = invoice.edi_document_ids.filtered(
                    lambda doc: doc.edi_format_id.code == "in_einvoice_1_03"
                ).attachment_id.raw
                if not l10n_in_send_json:
                    res[invoice] = {
                        "success": False,
                        "error": "Related E-Invoice not found!",
                    }
                    continue
                l10n_in_send_json = json.loads(l10n_in_send_json.decode("utf-8"))
                try:
                    response = service.cancel(
                        {
                            "Irn": l10n_in_send_json.get("Irn"),
                            "CnlRsn": invoice.l10n_in_edi_cancel_reason,
                            "CnlRem": invoice.l10n_in_edi_cancel_remarks,
                        }
                    )
                except UserError as e:
                    res[invoice] = {"success": False, "error": plaintext2html(e)}
                    continue
                json_dump = json.dumps(response.get("data"))
                json_name = "%s_cancel_einoivce.json" % (invoice.name.replace("/", "_"))
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": json_name,
                        "raw": json_dump.encode(),
                        "res_model": "account.move",
                        "res_id": invoice.id,
                        "mimetype": "application/json",
                        "description": _(
                            "Indian E-Invoice generated for the %s document.",
                            invoice.name,
                        ),
                    }
                )
                res[invoice] = {"success": True}
            return res
        return super()._post_invoice_edi(invoices)

    def _l10n_in_validate_partner(self, partner, is_company=False):
        self.ensure_one()
        message = str()
        if is_company and partner.country_id.code != "IN":
            message += "\n- Country should be India"
        if not re.match("^.{3,100}$", partner.street or ""):
            message += "\n- Street required min 3 and max 100 charactor"
        if partner.street2 and not re.match("^.{3,100}$", partner.street2):
            message += "\n- Street2 should be min 3 and max 100 charactor"
        if not re.match("^.{3,100}$", partner.city or ""):
            message += "\n- City required min 3 and max 100 charactor"
        if not re.match("^.{3,50}$", partner.state_id.name or ""):
            message += "\n- State required min 3 and max 50 charactor"
        if partner.country_id.code == "IN" and not re.match(
            "^[0-9]{6,}$", partner.zip or ""
        ):
            message += "\n- Zip code required 6 digites"
        if partner.phone and not re.match(
            "^[0-9]{10,12}$", self._extract_digits(partner.phone)
        ):
            message += "\n- Mobile number should be minimum 10 or maximum 12 digites"
        if partner.email and (
            not re.match(
                r"^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$", partner.email
            )
            or not re.match("^.{3,100}$", partner.email)
        ):
            message += (
                "\n- Email address should be valid and not more then 100 charactor"
            )

        if message:
            raise UserError(
                "Data not valid for the %s: %s\n%s"
                % (is_company and "Company" or "Customer", partner.name, message)
            )

    def _extract_digits(self, string):
        matches = re.findall(r"\d+", string)
        result = "".join(matches)
        return result

    def _l10n_in_prepare_json(self, invoice):
        values = self._l10n_in_prepare_edi_tax_details(invoice)
        generate_request_json = self.env["ir.ui.view"]._render_template(
            "l10n_in_edi.l10n_in_edi_einvoice_json_template", values
        )
        generate_request_json = generate_request_json.replace('&quot;','\\"')
        json_dump = json.dumps(safe_eval(generate_request_json))
        # Fix HTML Character Entities that use in data like company name "xyz & Sun"
        json_dump = html2text.html2text(json_dump)
        json_dump = json_dump.replace("\n", "")
        return json.loads(json_dump)

    def _l10n_in_prepare_edi_tax_details(self, invoice, in_foreign=False):
        res = super()._l10n_in_prepare_edi_tax_details(invoice, in_foreign)
        res.update({"supply_type": self._l10n_in_get_supply_type(invoice)})
        return res

    def _l10n_in_get_supply_type(self, invoice):
        supply_type = "B2B"
        if invoice.l10n_in_gst_treatment in (
            "overseas",
            "special_economic_zone",
        ) and self.env.ref("l10n_in.tax_report_line_igst") in invoice.mapped(
            "line_ids.tax_tag_ids.tax_report_line_ids"
        ):
            if invoice.l10n_in_gst_treatment == "overseas":
                supply_type = "EXPWP"
            if invoice.l10n_in_gst_treatment == "special_economic_zone":
                supply_type = "SEZWP"
        elif invoice.l10n_in_gst_treatment in ("overseas", "special_economic_zone"):
            if invoice.l10n_in_gst_treatment == "overseas":
                supply_type = "EXPWOP"
            if invoice.l10n_in_gst_treatment == "special_economic_zone":
                supply_type = "SEZWOP"
        elif invoice.l10n_in_gst_treatment == "deemed_export":
            supply_type = "DEXP"
        return supply_type
