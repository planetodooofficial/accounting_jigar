# -*- coding: utf-8 -*-

from odoo import api
from odoo import SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("select move.name ,t.move_id, t.response_json, t.cancel_response_json, t.status from l10n_in_einvoice_transaction_copy as t join account_move as move on move.id = t.move_id")
    for trn in cr.dictfetchall():
        attachment_id = env["ir.attachment"].create({
            "name": "%s_%s.josn"%(trn.get('name'),trn.get('status')),
            "raw": (status == 'cancel' and trn.get('cancel_response_json') or trn.get('response_json')).encode(),
            "res_model": "account.move",
            "res_id": trn.get('move_id'),
            "mimetype": "application/json",
        })
        env['account.edi.document'].create({
            'move_id': trn.get('move_id'),
            'edi_format_id': env.ref('l10n_in_edi.edi_in_einvoice_json_1_03').id,
            'attachment_id': attachment_id.id,
            'state': status == 'cancel' and 'cancelled' or 'sent',
        })
