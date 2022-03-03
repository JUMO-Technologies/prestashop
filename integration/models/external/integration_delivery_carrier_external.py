# See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class IntegrationDeliveryCarrierExternal(models.Model):
    _name = 'integration.delivery.carrier.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Delivery Carrier External'
