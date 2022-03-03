# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationProductTemplateExternal(models.Model):
    _name = 'integration.product.template.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Product Template External'
