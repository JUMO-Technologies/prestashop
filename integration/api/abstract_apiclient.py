# See LICENSE file for full copyright and licensing details.

from __future__ import absolute_import

from abc import ABCMeta, abstractmethod
import logging
from six import with_metaclass

_logger = logging.getLogger(__name__)


class AbsApiClient(with_metaclass(ABCMeta)):

    def __init__(self, settings):
        super(AbsApiClient, self).__init__()
        self._settings = settings

    def get_required_settings_value(self, key):
        value = self.get_settings_value(key)
        if not value:
            raise Exception(f'`{key}` is empty!')
        return value

    def get_settings_value(self, key):
        value = self._settings['fields'][key]['value']
        return value

    @abstractmethod
    def check_connection(self):
        return

    @abstractmethod
    def get_delivery_methods(self):
        return

    @abstractmethod
    def get_taxes(self):
        return

    @abstractmethod
    def get_account_tax_groups(self):
        return

    @abstractmethod
    def get_payment_methods(self):
        return

    @abstractmethod
    def get_languages(self):
        return

    @abstractmethod
    def get_attributes(self):
        return

    @abstractmethod
    def get_attribute_values(self):
        return

    @abstractmethod
    def get_countries(self):
        return

    @abstractmethod
    def get_states(self):
        return

    @abstractmethod
    def get_categories(self):
        return

    @abstractmethod
    def get_sale_order_statuses(self):
        return

    @abstractmethod
    def get_product_templates(self):
        return

    @abstractmethod
    def get_product_variants(self):
        return

    @abstractmethod
    def receive_orders(self):
        """
        Receive orders and prepare input file information

        :return:
        """
        return

    @abstractmethod
    def parse_order(self, input_file):
        """
        Parse order from input file. Mustn't make any calls to external service

        :param input_file:
        :return:
        """
        return

    @abstractmethod
    def export_template(self, template):
        return

    @abstractmethod
    def export_images(self, images):
        return

    @abstractmethod
    def export_attribute(self, attribute):
        return

    @abstractmethod
    def export_attribute_value(self, attribute_value):
        return

    @abstractmethod
    def export_category(self, category):
        return

    @abstractmethod
    def export_inventory(self, inventory):
        """Send actual QTY to the external services"""
        return

    @abstractmethod
    def export_tracking(self, tracking_data):
        return

    @abstractmethod
    def export_sale_order_status(self, order_id, status):
        return
