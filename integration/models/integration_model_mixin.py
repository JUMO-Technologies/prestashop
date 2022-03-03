# See LICENSE file for full copyright and licensing details.

from ..exceptions import NotMapped
from odoo import models, api


class IntegrationModelMixin(models.AbstractModel):
    _name = 'integration.model.mixin'
    _description = 'Integration Model Mixin'

    def try_to_external(self, integration):
        try:
            return self.to_external(integration)
        except NotMapped:
            return None

    def to_external(self, integration):
        self.ensure_one()
        mapping_model = self.env[f'integration.{self._name}.mapping']
        return mapping_model.to_external(integration, self)

    def to_external_or_export(self, integration):
        self.ensure_one()
        try:
            return self.to_external(integration)
        except NotMapped:
            return self.export_with_integration(integration)

    def to_export_format_or_export(self, integration):
        self.ensure_one()
        try:
            self.to_external(integration)
            return self.to_export_format(integration)
        except NotMapped:
            self.export_with_integration(integration)
            return self.to_export_format(integration)

    @api.model
    def from_external(self, integration, code, raise_error=True):
        mapping_model = self.env[f'integration.{self._name}.mapping']
        return mapping_model.to_odoo(integration, code, raise_error)

    @api.model
    def create_or_update_mapping(self, integration, odoo_object, external_object):
        mapping_model = self.env[f'integration.{self._name}.mapping']
        mapping = mapping_model.create_or_update_mapping(integration, odoo_object, external_object)
        return mapping

    def create_mapping(self, integration, code):
        mapping_model = self.env[f'integration.{self._name}.mapping']
        mapping = mapping_model.create_mapping(integration, self, code)
        return mapping

    def get_mapping(self, integration, code):
        mapping_model = self.env[f'integration.{self._name}.mapping']
        mapping = mapping_model.get_mapping(integration, code)
        return mapping

    def clear_mappings(self, integration):
        mapping_model = self.env[f'integration.{self._name}.mapping']
        mapping_model.clear_mappings(integration, self)

    @api.model
    def _check_fields_changed(self, fields_to_check, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            return bool(set(fields_to_check).intersection(set(vals.keys())))

        return False
