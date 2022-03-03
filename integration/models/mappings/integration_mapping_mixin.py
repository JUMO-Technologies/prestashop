# See LICENSE file for full copyright and licensing details.

from ...exceptions import NotMapped, NotMappedValue
from odoo import models, api, fields


class IntegrationMappingMixin(models.AbstractModel):
    _name = 'integration.mapping.mixin'
    _description = 'Integration Mapping Mixin'

    integration_id = fields.Many2one(
        comodel_name='sale.integration',
        required=True,
        ondelete='cascade',
    )

    failed_job_ids = fields.Many2many(
        comodel_name='queue.job',
    )

    def write(self, vals):
        result = super().write(vals)
        self.requeue_jobs_if_needed()
        return result

    def requeue_jobs_if_needed(self):
        jobs = self.mapped('failed_job_ids')
        for job in jobs:
            self._requeue_job_if_needed(job)

    @api.model
    def _requeue_job_if_needed(self, job):
        if job.state != 'failed':
            return

        for model_name in self.env:
            is_mapping_model = (
                model_name.startswith('integration.')
                and model_name.endswith('.mapping')
            )
            if not is_mapping_model:
                continue

            mappings = self.env[model_name].search([
                ('failed_job_ids', '=', job.id),
            ])

            for mapping in mappings:
                internal_field_name, external_field_name = mapping._mapping_fields
                internal_value = mapping[internal_field_name]
                external_value = mapping[external_field_name]

                if not internal_value or not external_value:
                    return

        job.requeue()

    @property
    def external_model(self):
        internal_field_name, external_field_name = self._mapping_fields
        external_model = self._get_model_by_field_name(external_field_name)
        return external_model

    @property
    def internal_model(self):
        internal_field_name, external_field_name = self._mapping_fields
        internal_model = self._get_model_by_field_name(internal_field_name)
        return internal_model

    def _get_model_by_field_name(self, field_name):
        field = self.fields_get(field_name)[field_name]
        model_name = field['relation']
        model = self.env[model_name]
        return model

    @api.model
    def create_mapping(self, integration, odoo_value, code):
        internal_field_name, external_field_name = self._mapping_fields

        external = self.external_model.create_or_update({
            'integration_id': integration.id,
            'code': code,
        })

        mapping = self.search([
            ('integration_id', '=', integration.id),
            (external_field_name, '=', external.id),
        ])

        if mapping:
            mapping_external = mapping[external_field_name]
            assert mapping_external.code == code, (mapping_external.code, code)  # noqa
            return mapping

        mapping = self.create({
            'integration_id': integration.id,
            internal_field_name: odoo_value.id,
            external_field_name: external.id,
        })

        return mapping

    @api.model
    def create_or_update_mapping(self, integration, odoo_object, external_object):
        odoo_object_id = False
        if odoo_object:
            odoo_object_id = odoo_object.id
        internal_field_name, external_field_name = self._mapping_fields
        mapping = self.search([
            ('integration_id', '=', integration.id),
            (external_field_name, '=', external_object.id),
        ])
        if not mapping:
            mapping = self.create({
                'integration_id': integration.id,
                external_field_name: external_object.id,
                internal_field_name: odoo_object_id,
            })
        else:
            mapping.write({internal_field_name: odoo_object_id})
        return mapping

    @api.model
    def get_mapping(self, integration, code):
        internal_field_name, external_field_name = self._mapping_fields

        external = self.external_model.search([
            ('integration_id', '=', integration.id),
            ('code', '=', code),
        ])

        mapping = self.search([
            ('integration_id', '=', integration.id),
            (external_field_name, '=', external.id),
        ])

        return mapping

    @api.model
    def to_odoo(self, integration, code, raise_error=True):
        mapping = self.get_mapping(integration, code)

        internal_field_name, external_field_name = self._mapping_fields
        record = getattr(mapping, internal_field_name)
        if not record and raise_error:
            value = NotMappedValue(self.internal_model._name, code)
            msg = '%s %s' % (self.internal_model._name, code)
            raise NotMapped(msg, value)

        return record

    @api.model
    def to_external(self, integration, odoo_value):
        internal_field_name, external_field_name = self._mapping_fields

        mapping = self.search([
            ('integration_id', '=', integration.id),
            (internal_field_name, '=', odoo_value.id),
        ], order='id desc', limit=1)

        if not mapping:
            # todo: refactor exception warning
            raise NotMapped('%s %s %s' % (self, odoo_value, odoo_value.name))

        return getattr(mapping, external_field_name).code

    def bind_odoo(self, record):
        self.ensure_one()
        internal_field_name, _ = self._mapping_fields
        self[internal_field_name] = record

    def clear_mappings(self, integration, records=None):
        internal_field_name, external_field_name = self._mapping_fields

        domain = [
            ('integration_id', '=', integration.id),
        ]
        if records:
            domain.append((internal_field_name, 'in', records.ids))

        mappings = self.search(domain)
        mappings.unlink()
