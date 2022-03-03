# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationAccountTaxExternal(models.Model):
    _name = 'integration.account.tax.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Account Tax External'
