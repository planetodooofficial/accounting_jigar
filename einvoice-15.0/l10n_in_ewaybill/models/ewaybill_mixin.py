# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import UserError

TEMPLATES = {
    "generate": "l10n_in_ewaybill.l10n_in_ewaybill_generate_json",
    "cancel": "l10n_in_ewaybill.l10n_in_ewaybill_cancel_json",
    "update_partb": "l10n_in_ewaybill.l10n_in_ewaybill_update_part_b_json",
    "extend_date": "l10n_in_ewaybill.l10n_in_ewaybill_extend_json",
}


class EwayBillType(models.Model):
    _name = "l10n.in.ewaybill.type"
    _description = "eWaybill Document Type"

    name = fields.Char("Document Type")
    code = fields.Char("Code")
    allowed_in_supply_type = fields.Selection(
        [
            ("both", "Incoming and Outgoing"),
            ("out", "Outgoing"),
            ("in", "Incoming"),
        ],
        string="Allowed in supply type",
    )
    allowed_in_document = fields.Selection(
        [("invoice", "Invoice"), ("stock", "Stock")], string="Allowed in Document"
    )
    active = fields.Boolean("Active", default=True)

    child_type_ids = fields.Many2many(
        "l10n.in.ewaybill.type",
        "rel_ewaybill_type_subtype",
        "type_id",
        "subtype_id",
        "Subtype",
    )
    parent_type_ids = fields.Many2many(
        "l10n.in.ewaybill.type",
        "rel_ewaybill_type_subtype",
        "subtype_id",
        "type_id",
        "Parent Types",
    )


class L10nInEwayBillMixin(models.AbstractModel):
    _name = "l10n.in.ewaybill.mixin"
    _description = "Base of eWaybill"

    l10n_in_ewaybill_type_id = fields.Many2one("l10n.in.ewaybill.type", "Document Type")
    l10n_in_ewaybill_subtype_id = fields.Many2one(
        "l10n.in.ewaybill.type", "Sub Supply Type"
    )
    l10n_in_ewaybill_subtype_code = fields.Char(
        "Sub Supply Type Code", related="l10n_in_ewaybill_subtype_id.code"
    )
    l10n_in_ewaybill_sub_supply_desc = fields.Char("Sub Supply Description")

    # In Stock onlu "Regular" and "Bill From-Dispatch From" is supported
    l10n_in_ewaybill_transaction_type = fields.Selection(
        [
            ("1", "Regular"),
            ("2", "Bill To-Ship To"),
            ("3", "Bill From-Dispatch From"),
            ("4", "Combination of 2 and 3"),
        ],
        string="Ewaybill Transaction Type",
    )

    l10n_in_ewaybill_mode = fields.Selection(
        [
            ("0", "Managed by Transporter"),
            ("1", "By Road"),
            ("2", "Rail"),
            ("3", "Air"),
            ("4", "Ship"),
        ],
        string="Transportation Mode",
    )

    l10n_in_ewaybill_vehicle_type = fields.Selection(
        [
            ("R", "Regular"),
            ("O", "ODC"),
        ],
        string="Vehicle Type",
    )

    l10n_in_ewaybill_transporter_id = fields.Many2one("res.partner", "Transporter")

    l10n_in_ewaybill_distance = fields.Integer("Distance")
    l10n_in_ewaybill_vehicle_no = fields.Char("Vehicle Number")

    l10n_in_ewaybill_transporter_doc_no = fields.Char(
        "Document Number",
        help="""Transport document number.
If it is more than 15 chars, last 15 chars may be entered""",
    )
    l10n_in_ewaybill_transporter_doc_date = fields.Date(
        "Document Date", help="Date on the transporter document"
    )

    l10n_in_ewaybill_number = fields.Char(
        compute="_compute_l10n_in_ewaybill_details", string="eWaybill Number"
    )
    l10n_in_ewaybill_valid_upto = fields.Datetime(
        compute="_compute_l10n_in_ewaybill_details", string="Valid Upto"
    )
    l10n_in_ewaybill_state = fields.Selection(
        [
            ("not_submited", "Not Submited"),
            ("submited", "Submited"),
            ("cancelled", "Cancelled"),
        ],
        string="eWaybill Status",
        compute="_compute_l10n_in_ewaybill_details",
    )

    # TO BE OVERWRITTEN
    def _get_ewaybill_transaction_domain(self):
        return []

    def _compute_l10n_in_ewaybill_details(self):
        for record in self:
            transaction = self.env["l10n.in.ewaybill.transaction"].search(
                record._get_ewaybill_transaction_domain()
                + [("request_type", "!=", "update_partb")],
                limit=1,
            )
            record.l10n_in_ewaybill_number = transaction.ewaybill_number
            # if eway bill is cancelled then not set valid_upto because is meaningless
            if transaction and transaction.request_type == "cancel":
                record.l10n_in_ewaybill_valid_upto = False
                record.l10n_in_ewaybill_state = "cancelled"
            elif transaction and transaction.request_type != "cancel":
                record.l10n_in_ewaybill_valid_upto = transaction.ewaybill_valid_upto
                record.l10n_in_ewaybill_state = "submited"
            else:
                record.l10n_in_ewaybill_state = "not_submited"
                record.l10n_in_ewaybill_valid_upto = False

    @api.model
    def _validate_ewaybill_partner(self, partner, prefix):
        message = str()
        if partner and not re.match("^[0-9]{6,}$", partner.zip or ""):
            message += "\n- %s(%s) required Pincode" % (prefix, partner.name)
        if partner and not partner.state_id.name:
            message += "\n- %s(%s) required State" % (prefix, partner.name)
        return message

    def _prepare_validate_ewaybill_message(self):
        self.ensure_one()
        message = str()
        required_fields = [
            "l10n_in_ewaybill_transaction_type",
            "l10n_in_ewaybill_type_id",
            "l10n_in_ewaybill_subtype_id",
            "l10n_in_ewaybill_mode",
        ]
        for field_name in required_fields:
            field = self.env["ir.model.fields"]._get(self._name, field_name)
            if field and not self[field_name]:
                message += "\n- %s is Required" % (field.field_description)
        return message

    def _validate_l10n_in_ewaybill(self):
        self.ensure_one()
        message = self._prepare_validate_ewaybill_message()
        if message:
            raise UserError(_(message))
        return True

    # TO BE OVERWRITTEN
    def _generate_ewaybill_transaction(self, values):
        return self.env["l10n.in.ewaybill.transaction"].create(values)

    def button_l10n_in_submit_ewaybill(self):
        self.ensure_one()
        self._validate_l10n_in_ewaybill()

        ewaybill = self._generate_ewaybill_transaction({"request_type": "generate"})
        ewaybill.submit()
        response_json = ewaybill._get_response_json_dict()
        if response_json.get("alert", False):
            msg_subject = _("E-waybill Alert")
            odoobot_id = self.env["ir.model.data"]._xmlid_to_res_id("base.partner_root")
            self.message_post(
                body=response_json.get("alert", False),
                author_id=odoobot_id,
                subject=msg_subject,
            )

    def button_l10n_in_cancel_ewaybill(self):
        self.ensure_one()
        return {
            "name": _("Cancel Eway Bill"),
            "res_model": "l10n.in.ewaybill.cancel",
            "view_mode": "form",
            "view_id": self.env.ref("l10n_in_ewaybill.view_cancel_ewaybill").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def button_l10n_in_ewaybill_update_part_b(self):
        self.ensure_one()
        return {
            "name": _("Update Part-B or Transporter id"),
            "res_model": "l10n.in.ewaybill.update.partb",
            "view_mode": "form",
            "view_id": self.env.ref("l10n_in_ewaybill.view_update_part_b").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def button_l10n_in_extend_ewaybill(self):
        self.ensure_one()
        return {
            "name": _("Extend Eway Bill"),
            "res_model": "l10n.in.ewaybill.extend",
            "view_mode": "form",
            "view_id": self.env.ref("l10n_in_ewaybill.view_extend_ewaybill").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def action_view_ewaybills(self):
        self.ensure_one()
        domain = self._get_ewaybill_transaction_domain()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_in_ewaybill.action_ewaybill_list"
        )
        context = literal_eval(action["context"])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)
