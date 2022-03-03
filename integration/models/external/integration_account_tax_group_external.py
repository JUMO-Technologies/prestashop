# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationAccountTaxGroupExternal(models.Model):
    _name = 'integration.account.tax.group.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Account Tax Group External'
