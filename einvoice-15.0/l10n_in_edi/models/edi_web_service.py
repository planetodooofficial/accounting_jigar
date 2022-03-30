# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning

from odoo.addons.iap import jsonrpc

DEFAULT_ENDPOINT = "https://einvoice.odoo.co.in"

import logging

_logger = logging.getLogger(__name__)


class L10nInEdiWebService(models.Model):
    _name = "l10n.in.edi.web.service"
    _description = "Indian eInvoice Service"

    company_id = fields.Many2one("res.company", string="Company")
    token = fields.Char("Token")
    token_validity = fields.Datetime("Valid Until")
    is_token_valid = fields.Boolean(compute="_is_token_valid", string="Valid Token")

    def _is_token_valid(self):
        for service in self:
            if (
                service.token_validity
                and service.token_validity > fields.Datetime.now()
            ):
                service.is_token_valid = True
            else:
                service.is_token_valid = False

    def _raise_error_for_setup(self, company):
        msg = "E-invoice IAP is not yet configured for company %s.\n" % (company.name)
        if self.env.is_admin():
            action = self.env.ref("base_setup.action_general_configuration")
            raise RedirectWarning(
                msg + "Please configure.", action.id, _("Go to Settings")
            )
        else:
            raise UserError(msg + "Please contact your administrator.")

    @api.model
    def get_service(self, company, create_if_not_found=False):
        service = self.search([("company_id", "=", company.id)], limit=1)
        if not create_if_not_found and not service:
            self._raise_error_for_setup(company)
        if not service:
            service = self.create({"company_id": company.id})
        return service

    def _connect_to_server(self, url_path, params):
        self.ensure_one()
        user_token = self.env["iap.account"].get("einvoice_india")
        params.update(
            {
                "account_token": user_token.account_token,
                "username": self.company_id.l10n_in_edi_username,
                "gstin": self.company_id.vat,
            }
        )
        endpoint = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("einvoice_india.endpoint", DEFAULT_ENDPOINT)
        )
        url = "%s%s" % (endpoint, url_path)
        return jsonrpc(url, params=params, timeout=25)

    def get_token(self):
        self.ensure_one()
        if self.is_token_valid:
            return self.token
        elif (
            self.company_id.l10n_in_edi_username
            and self.company_id.sudo().l10n_in_edi_password
        ):
            self.authenticate()
            return self.token
        else:
            self._raise_error_for_setup(self.company_id)

    def setup(self):
        # this is use first time to setup in server
        self.ensure_one()
        params = {"password": self.company_id.l10n_in_edi_password}
        response = self._connect_to_server(
            url_path="/iap/einvoice/setup", params=params
        )
        self.token_validity = fields.Datetime.to_datetime(
            response["data"]["TokenExpiry"]
        ) - timedelta(hours=5, minutes=30, seconds=00)
        self.token = response["data"]["AuthToken"]

    def authenticate(self):
        self.ensure_one()
        params = {"password": self.company_id.sudo().l10n_in_edi_password}
        response = self._connect_to_server(
            url_path="/iap/einvoice/authenticate", params=params
        )
        # validity data-time in Indian standard time(UTC+05:30) so remove that gap and store in odoo
        self.token_validity = fields.Datetime.to_datetime(
            response["data"]["TokenExpiry"]
        ) - timedelta(hours=5, minutes=30, seconds=00)
        self.token = response["data"]["AuthToken"]

    def generate(self, json_payload):
        self.ensure_one()
        token = self.get_token()
        params = {
            "auth_token": token,
            "json_payload": json_payload,
        }
        return self._connect_to_server(
            url_path="/iap/einvoice/type/GENERATE/version/V1_03", params=params
        )

    def get_irn_by_details(self, json_payload):
        self.ensure_one()
        token = self.get_token()
        params = {
            "auth_token": token,
        }
        params.update(json_payload)
        return self._connect_to_server(
            url_path="/iap/einvoice/type/GETIRNBYDOCDETAILS/version/V1_03",
            params=params,
        )

    def cancel(self, json_payload):
        self.ensure_one()
        token = self.get_token()
        params = {
            "auth_token": token,
            "json_payload": json_payload,
        }
        return self._connect_to_server(
            url_path="/iap/einvoice/type/CANCEL/version/V1_03", params=params
        )
