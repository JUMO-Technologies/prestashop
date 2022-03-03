# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationProductPublicCategoryExternal(models.Model):
    _name = 'integration.product.public.category.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Product Public Category External'
