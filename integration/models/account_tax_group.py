# See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountTaxGroup(models.Model):
    _name = 'account.tax.group'
    _inherit = ['account.tax.group', 'integration.model.mixin']
