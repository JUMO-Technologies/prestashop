#  See LICENSE file for full copyright and licensing details.

import pytz
from odoo import models, fields, api
from ..prestashop_api import PrestaShopApiClient

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class SaleIntegration(models.Model):
    _inherit = 'sale.integration'

    type_api = fields.Selection(
        selection_add=[('prestashop', 'PrestaShop')],
        ondelete={
            'prestashop': 'cascade',
        },
    )

    presta_last_receive_orders_datetime = fields.Char(
        compute='_compute_presta_last_receive_orders_datetime',
    )

    @api.depends('last_receive_orders_datetime')
    def _compute_presta_last_receive_orders_datetime(self):
        for integration in self:
            value = ''

            if integration.type_api == 'prestashop':
                ps_timezone = integration.get_settings_value('PS_TIMEZONE')
                if ps_timezone:
                    timezone = pytz.timezone(ps_timezone)
                    value = integration.last_receive_orders_datetime.astimezone(
                        timezone,
                    )
                    value = value.strftime(DATETIME_FORMAT)

            integration.presta_last_receive_orders_datetime = value

    def get_class(self):
        self.ensure_one()
        if self.type_api == 'prestashop':
            return PrestaShopApiClient

        return super().get_class()

    def action_active(self):
        self.ensure_one()
        result = super().action_active()

        if self.type_api == 'prestashop':
            adapter = self._build_adapter()
            ps_configuration = adapter._client.model('configuration')
            ps_timezone = ps_configuration.search({'name': 'PS_TIMEZONE'}).value
            self.set_settings_value('PS_TIMEZONE', ps_timezone)

        return result
