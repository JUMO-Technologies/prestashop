# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationProductProductExternal(models.Model):
    _name = 'integration.product.product.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Product Product External'
