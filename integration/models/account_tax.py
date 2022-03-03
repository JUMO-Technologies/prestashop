# See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountTax(models.Model):
    _name = 'account.tax'
    _inherit = ['account.tax', 'integration.model.mixin']
