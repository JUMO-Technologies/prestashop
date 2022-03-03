# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ...exceptions import NoReferenceFieldDefined
import logging

_logger = logging.getLogger(__name__)


class IntegrationExternalMixin(models.AbstractModel):
    _name = 'integration.external.mixin'
    _description = 'Integration External Mixin'

    integration_id = fields.Many2one(
        comodel_name='sale.integration',
        required=True,
        ondelete='cascade',
    )

    code = fields.Char(
        required=True,
    )

    name = fields.Char(
        string='External Name',
        help='Contains name of the External Object in selected Integration'
    )

    external_reference = fields.Char(
        string='External Reference',
        help='Contains unique code of the External Object in the external '
             'system. Used for automated mapping',
    )
    _sql_constraints = [
        (
            'uniq_code',
            'unique(integration_id, code)',
            'Code should be unique'
        ),
        (
            'uniq_code',
            'unique(integration_id, external_reference)',
            'External Reference should be unique'
        ),
    ]

    @api.model
    def create_or_update(self, vals):
        domain = [
            ('integration_id', '=', vals['integration_id']),
            ('code', '=', vals['code']),
        ]

        record = self.search(domain, limit=1)
        if record:
            record.write(vals)
            return record
        else:
            return self.create(vals)

    def name_get(self):
        result = []
        for rec in self:
            if rec.external_reference:
                result.append((rec.id, '(%s)[%s] %s'
                               % (rec.code, rec.external_reference, rec.name)))
            else:
                result.append((rec.id, '(%s) %s' % (rec.code, rec.name)))
        return result

    def try_map_by_external_reference(self, odoo_model, odoo_search_domain=False):
        self.ensure_one()
        reference_field_name = getattr(odoo_model, '_internal_reference_field', None)
        if not reference_field_name:
            raise NoReferenceFieldDefined(
                _('No _internal_reference_field field defined for model %s') % self._name
            )

        odoo_object = None
        if self.external_reference:
            odoo_id = odoo_model.from_external(self.integration_id,
                                               self.code,
                                               raise_error=False)
            if odoo_id:
                # Id we found existing mapping, we do not need to do anything
                return

            search_domain = [(reference_field_name, '=ilike', self.external_reference)]
            # We can redefine domain if we need it
            if odoo_search_domain:
                search_domain = odoo_search_domain
            odoo_object = odoo_model.search(search_domain)
            if len(odoo_object) > 1:
                # If found more than one object we need to skip
                odoo_object = None

        odoo_model.create_or_update_mapping(self.integration_id, odoo_object, self)

    @api.model
    def fix_unmapped(self, integration):
        # Method that should be overriden in needed external models
        pass

    def create_mapping(self, odoo_record):
        self.ensure_one()

        odoo_record.create_mapping(
            self.integration_id,
            self.code,
        )
