# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_in_edi_cancel_reason = fields.Selection(
        selection=[
            ("1", "Duplicate"),
            ("2", "Data Entry Mistake"),
            ("3", "Order Cancelled"),
            ("4", "Others"),
        ],
        string="Cancel reason",
        copy=False,
    )
    l10n_in_edi_cancel_remarks = fields.Char("Cancel remarks", copy=False)

    def _extract_digits(self, string):
        matches = re.findall(r"\d+", string)
        result = "".join(matches)
        return result

    def button_cancel_posted_moves(self):
        """Mark the edi.document related to this move to be canceled."""
        reason_and_remarks_not_set = self.env["account.move"]
        is_cancelled = False
        for move in self:
            # check any Indian E-invoice is submitted
            send_l10n_in_edi = move.edi_document_ids.filtered(
                lambda doc: doc.edi_format_id.code == "in_einvoice_1_03"
                and doc.state == "sent"
            )
            if send_l10n_in_edi:
                is_cancelled = True
            # check submitted E-invoice does not have reason and remarks
            # because it's needed to cancel E-invoice
            if send_l10n_in_edi and (
                not move.l10n_in_edi_cancel_reason
                or not move.l10n_in_edi_cancel_remarks
            ):
                reason_and_remarks_not_set += move
        if reason_and_remarks_not_set:
            raise UserError(
                "To cancel E-invoice set cancel reason and remarks in invoices: \n%s"
                % ("\n".join(reason_and_remarks_not_set.mapped("name")))
            )
        res = super().button_cancel_posted_moves()
        if is_cancelled:
            self.action_process_edi_web_services()
        return res

    def action_process_edi_web_services_confirm(self):
        # before confirm check edi service is activated
        for move in self:
            service = self.env["l10n.in.edi.web.service"].get_service(move.company_id)
            token = service.get_token()
        return super().action_process_edi_web_services_confirm()
