# See LICENSE file for full copyright and licensing details.

import json
import base64

from cerberus import Validator
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleIntegration(models.Model):
    _name = 'sale.integration'
    _description = 'Sale Integration'

    name = fields.Char(
        required=True,
    )

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda self: self.env.company,
    )

    type_api = fields.Selection(
        [('no_api', 'Not Use API')],
        string='Api service',
        required=True,
        ondelete={
            'no_api': 'cascade',
        },
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
        ],
        string='Status',
        required=True,
        default='draft',
        inverse='_inverse_state',
    )

    field_ids = fields.One2many(
        'sale.integration.api.field',
        'sia_id',
        string='Fields',
    )

    test_method = fields.Selection(
        '_get_test_method',
        string='Test Method',
    )

    location_ids = fields.Many2many(
        comodel_name='stock.location',
        string='Locations',
        domain=[
            ('usage', '=', 'internal'),
        ],
    )

    last_receive_orders_datetime = fields.Datetime(
        default=fields.Datetime.now,
    )
    receive_orders_cron_id = fields.Many2one(
        comodel_name='ir.cron',
    )
    sale_order_auto_confirm = fields.Boolean('Auto Confirm Created Sale Orders')

    export_template_job_enabled = fields.Boolean(
        string='Export Product Template Job Enabled',
        default=False,
    )
    export_inventory_job_enabled = fields.Boolean(
        default=False,
    )
    export_tracking_job_enabled = fields.Boolean(
        default=False,
    )
    export_sale_order_status_job_enabled = fields.Boolean(
        default=False,
    )

    product_ids = fields.Many2many(
        'product.template', 'sale_integration_product', 'sale_integration_id', 'product_id',
        'Products', copy=False, check_company=True)

    def action_active(self):
        self.ensure_one()
        self.action_check_connection(raise_success=False)
        self.state = 'active'

    def action_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def action_check_connection(self, raise_success=True):
        self.ensure_one()
        adapter = self._build_adapter()

        try:
            connection_ok = adapter.check_connection()
        except Exception as e:
            raise UserError(e) from e

        if connection_ok:
            if raise_success:
                raise UserError(_('Connected'))
        else:
            raise UserError(_('Connection failed'))

    def _inverse_state(self):
        for integration in self:
            if not integration.receive_orders_cron_id:
                cron = integration._create_receive_orders_cron()
                integration.receive_orders_cron_id = cron

            is_cron_active = integration.state == 'active'
            integration.receive_orders_cron_id.active = is_cron_active

    def _create_receive_orders_cron(self):
        self.ensure_one()
        vals = {
            'name': f'Integration: {self.name} Receive Orders',
            'model_id': self.env.ref('integration.model_sale_integration').id,
            'numbercall': -1,
            'interval_type': 'minutes',
            'interval_number': 5,
            'code': f'model.browse({self.id}).integrationApiReceiveOrders()',
        }
        cron = self.env['ir.cron'].create(vals)
        return cron

    @api.model
    def get_integrations(self, job, company):
        domain = [
            ('state', '=', 'active'),
            (f'{job}_job_enabled', '=', True),
        ]

        if company:
            domain.append(('company_id', '=', company.id))

        integrations = self.search(domain)
        return integrations

    def job_enabled(self, name):
        self.ensure_one()

        if self.state != 'active':
            return False

        job_enabled_field_name = f'{name}_job_enabled'
        result = self[job_enabled_field_name]
        return result

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.write_settings_fields(vals)
        res.create_fields_mapping_for_integration()
        return self.browse(res.id)

    def write(self, vals):
        self.ensure_one()
        res = super().write(vals)
        ctx = self.env.context.copy()
        if not ctx.get('write_settings_fields'):
            res = self.write_settings_fields(vals)
        return res

    def create_fields_mapping_for_integration(self):
        ecommerce_fields = self.env['product.ecommerce.field']\
            .search([('type_api', '=', self.type_api)])

        for field in ecommerce_fields:
            create_vals = {
                'ecommerce_field_id' : field.id,
                'integration_id': self.id,
                'send_on_update': field.default_for_update,
            }
            self.env['product.ecommerce.field.mapping'].create(create_vals)

    def write_settings_fields(self, vals):
        self.ensure_one()

        res = True
        if 'type_api' in vals:
            settings_fields = self.get_default_settings_fields(vals['type_api'])
        else:
            settings_fields = self.get_default_settings_fields()

        if settings_fields is not None and settings_fields:
            exists_fields = self.field_ids.to_dictionary()
            settings_fields = self.convert_settings_fields(settings_fields)
            new_fields = {
                'field_ids': [
                    (0, 0, {
                        'name': field_name,
                        'description': field['description'],
                        'value': field['value'],
                        'eval': field['eval'],
                    })
                    for field_name, field in settings_fields.items()
                    if field_name not in exists_fields
                ]
            }
            ctx = self.env.context.copy()
            ctx.update({'write_settings_fields': True})
            res = self.with_context(ctx).write(new_fields)

        return res

    def get_settings_value(self, key):
        self.ensure_one()
        field = self.get_settings_field(key)
        value = field.value
        return value

    def set_settings_value(self, key, value):
        self.ensure_one()
        field = self.get_settings_field(key)
        field.value = value

    def get_settings_field(self, key):
        self.ensure_one()

        field = self.field_ids.search([
            ('sia_id', '=', self.id),
            ('name', '=', key),
        ], limit=1)

        if not field:
            raise ValueError(f'Settings field with key = {key} is not found!')

        return field

    @api.model
    def convert_settings_fields(self, settings_fields):
        return {
            field[0]: {
                'name': field[0],
                'description': field[1],
                'value': field[2],
                'eval': field[3] if len(field) > 3 else False
            }
            for field in settings_fields
        }

    @api.model
    def get_default_settings_fields(self, type_api=None):
        return getattr(self.get_class(), 'settings_fields')

    def integrationApiImportData(self):
        self.integrationApiImportDeliveryMethods()
        self.integrationApiImportTaxes()
        self.integrationApiImportAccountTaxGroups()
        self.integrationApiImportPaymentMethods()
        self.integrationApiImportLanguages()
        self.integrationApiImportAttributes()
        self.integrationApiImportAttributeValues()
        self.integrationApiImportCountries()
        self.integrationApiImportStates()
        self.integrationApiImportCategories()
        self.integrationApiImportSaleOrderStatuses()
        self.integrationApiImportProductsTemplate()
        self.integrationApiImportProductsVariants()

    def integrationApiImportDeliveryMethods(self):
        external_records = self._import_external(
            'integration.delivery.carrier.external',
            'get_delivery_methods',
        )
        self._map_external('delivery.carrier')
        return external_records

    def integrationApiImportTaxes(self):
        external_records = self._import_external(
            'integration.account.tax.external',
            'get_taxes',
        )
        return external_records

    def integrationApiImportAccountTaxGroups(self):
        external_records = self._import_external(
            'integration.account.tax.group.external',
            'get_account_tax_groups',
        )
        return external_records

    def integrationApiImportPaymentMethods(self):
        external_records = self._import_external(
            'integration.sale.order.payment.method.external',
            'get_payment_methods',
        )
        self._map_external('sale.order.payment.method')
        return external_records

    def integrationApiImportLanguages(self):
        external_records = self._import_external(
            'integration.res.lang.external',
            'get_languages',
        )
        self._map_external('res.lang')
        return external_records

    def integrationApiImportAttributes(self):
        external_records = self._import_external(
            'integration.product.attribute.external',
            'get_attributes',
        )
        return external_records

    def integrationApiImportAttributeValues(self):
        external_records = self._import_external(
            'integration.product.attribute.value.external',
            'get_attribute_values',
        )
        return external_records

    def integrationApiImportCountries(self):
        external_records = self._import_external(
            'integration.res.country.external',
            'get_countries',
        )
        self._map_external('res.country')
        return external_records

    def integrationApiImportStates(self):
        external_records = self._import_external(
            'integration.res.country.state.external',
            'get_states',
        )
        self._map_external('res.country.state')
        return external_records

    def integrationApiImportCategories(self):
        external_records = self._import_external(
            'integration.product.public.category.external',
            'get_categories',
        )
        return external_records

    def integrationApiImportProductsTemplate(self):
        external_records = self._import_external(
            'integration.product.template.external',
            'get_product_templates',
        )
        return external_records

    def integrationApiImportProductsVariants(self):
        external_records = self._import_external(
            'integration.product.product.external',
            'get_product_variants',
        )
        return external_records

    def integrationApiImportSaleOrderStatuses(self):
        external_records = self._import_external(
            'integration.sale.order.sub.status.external',
            'get_sale_order_statuses',
        )
        self._map_external('sale.order.sub.status')
        return external_records

    def _import_external(self, model, method):
        self.ensure_one()
        adapter = self._build_adapter()
        adapter_method = getattr(adapter, method)
        adapter_external_records = adapter_method()

        external_records = self.env[model]
        for adapter_external_record in adapter_external_records:
            name = adapter_external_record.get('name')
            if not name:
                name = adapter_external_record['id']
            external_record = self.env[model].create_or_update({
                'integration_id': self.id,
                'code': adapter_external_record['id'],
                'name': name,
                'external_reference': adapter_external_record.get('external_reference'),
            })
            external_records += external_record

        return external_records

    def _map_external(self, odoo_model_name):
        external_model = self.env[f'integration.{odoo_model_name}.external']
        all_external_records = external_model.search([
            ('integration_id', '=', self.id)
        ])
        for external_record in all_external_records:
            external_record.try_map_by_external_reference(self.env[odoo_model_name])
        external_model.fix_unmapped(self)

    def export_template(self, template, *, export_images=False):
        self.ensure_one()
        adapter = self._build_adapter()

        mappings = adapter.export_template(
            template.to_export_format(self),
        )

        for mapping in mappings:
            record = self.env[mapping['model']].browse(mapping['id'])
            record.create_mapping(self, mapping['external_id'])

        if export_images:
            self.export_images(template)

        if template.type == 'product':
            self.export_inventory(template)

        external_code = template.to_external(self)
        return external_code

    def calculate_field_value(self, odoo_object, ecommerce_field):
        self.ensure_one()
        converter_method = getattr(self, '_get_{}_value'.format(ecommerce_field.value_converter))
        if not converter_method:
            raise UserError(
                _(
                    'There is no method defined for converter %s'
                ) % ecommerce_field.value_converter
            )
        return converter_method(odoo_object, ecommerce_field)

    def _get_simple_value(self, odoo_object, ecommerce_field):
        return getattr(odoo_object, ecommerce_field.odoo_field_id.name)

    def _get_translatable_field_value(self, odoo_object, ecomm_field):
        return self.convert_translated_field_to_integration_format(odoo_object,
                                                                   ecomm_field.odoo_field_id.name)

    def _get_python_method_value(self, odoo_object, ecommerce_field):
        custom_python_method = getattr(odoo_object, ecommerce_field.method_name)
        if not custom_python_method:
            raise UserError(
                _(
                    'There is no method %s defined for object %s'
                ) % (ecommerce_field.method_name, odoo_object._name)
            )
        return custom_python_method(self)

    def convert_translated_field_to_integration_format(self, record, field):
        self.ensure_one()

        language_mappings = self.env['integration.res.lang.mapping'].search([
            ('integration_id', '=', self.id)
        ])

        translations = {}
        for language_mapping in language_mappings:
            external_code = language_mapping.external_language_id.code
            translations[external_code] = getattr(
                record.with_context(lang=language_mapping.language_id.code),
                field,
            )

        return translations

    def export_images(self, template):
        self.ensure_one()
        adapter = self._build_adapter()
        export_images_data = template.to_images_export_format(self)
        adapter.export_images(export_images_data)

    def get_inventory(self, templates):
        inventory = {}

        self._clear_free_qty_cache(templates)

        for product in templates.product_variant_ids:
            # if location_ids are empty odoo will return all inventory
            # so to prevent this we check location_ids here
            if self.location_ids:
                quantity = product.with_context(location=self.location_ids.ids).free_qty
            else:
                quantity = 0

            product_external_id = product.to_external(self)
            inventory[product_external_id] = {
                'qty': quantity,
            }

        return inventory

    def _clear_free_qty_cache(self, templates):
        """
        invalidate cache for all product's free_qty
        it seems that odoo doesn't recompute free_qty.
        if we read free_qty, then change it, then read again.
        doesn't seem to be a real case
        (usually export_inventory is done in single transaction).
        added to fix test, but I don't think that it affects performance very much.
        """
        self.env['product.product'].invalidate_cache(
            ['free_qty'], templates.product_variant_ids.ids
        )

    def export_inventory(self, templates):
        self.ensure_one()

        inventory = self.get_inventory(templates)

        adapter = self._build_adapter()
        adapter.export_inventory(inventory)

        return True

    def export_tracking(self, picking):
        self.ensure_one()

        adapter = self._build_adapter()
        tracking_data = picking.to_export_format(self)
        adapter.export_tracking(tracking_data)
        # After successful tracking export, add corresponding flag to the picking
        picking.tracking_exported = True

    def export_sale_order_status(self, order):
        self.ensure_one()

        adapter = self._build_adapter()
        adapter.export_sale_order_status(
            order.to_external(self),
            order.sub_status_id.to_external(self),
        )

    def export_attribute(self, attribute):
        self.ensure_one()
        adapter = self._build_adapter()

        code = adapter.export_attribute(attribute.to_export_format(self))

        attribute.create_mapping(self, code)

        return code

    def export_attribute_value(self, attribute_value):
        self.ensure_one()
        adapter = self._build_adapter()

        code = adapter.export_attribute_value(
            attribute_value.to_export_format(self)
        )

        attribute_value.create_mapping(self, code)

        return code

    def export_category(self, category):
        self.ensure_one()
        adapter = self._build_adapter()

        code = adapter.export_category(category.to_export_format(self))
        category.create_mapping(self, code)

        return code

    def _build_adapter(self):
        self.ensure_one()
        settings = self.to_dictionary()
        adapter = settings['class'](settings)
        return adapter

    def to_dictionary(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type_api': self.type_api,
            'class': self.get_class(),
            'fields': self.field_ids.to_dictionary(),
        }

    def integrationApiReceiveOrders(self):
        self.ensure_one()

        adapter = self._build_adapter()
        input_files = adapter.receive_orders()

        created_input_files = self.env['sale.integration.input.file']
        for input_file in input_files:
            self._validate_input_file_format(input_file)

            external_id = input_file['id']
            exists = self.env['sale.integration.input.file'].search([
                ('name', '=', external_id),
                ('si_id', '=', self.id),
            ], limit=1)

            if exists:
                continue

            input_file_data = input_file['data']
            input_file_json = json.dumps(input_file_data)
            input_file_base64 = base64.b64encode(input_file_json.encode())
            created_input_files += self.env['sale.integration.input.file'].create({
                'name': external_id,
                'si_id': self.id,
                'file': input_file_base64,
            })

        self.update_last_receive_orders_datetime_to_now()

        return created_input_files

    def update_last_receive_orders_datetime_to_now(self):
        self.last_receive_orders_datetime = datetime.now()

    def trigger_create_order(self, input_files):
        jobs = self.env['queue.job']

        for input_file in input_files:
            integration = input_file.si_id
            job = integration.with_delay().create_order(input_file)
            jobs += job.db_record()

        return jobs

    def trigger_link_all(self):
        # method to trigger linking of integration to all products
        integrations_to_add = [(4, integration.id) for integration in self]
        product_templates = self.env['product.template'].search([])
        product_templates.write({
            'integration_ids': integrations_to_add,
        })

    def trigger_unlink_all(self):
        # method to trigger linking of integration to all products
        integrations_to_add = [(3, integration.id) for integration in self]
        product_templates = self.env['product.template'].search([])
        product_templates.write({
            'integration_ids': integrations_to_add,
        })

    def parse_order(self, input_file):
        self.ensure_one()

        adapter = self._build_adapter()

        input_file_data = input_file.to_dict()
        order_data = adapter.parse_order(
            input_file_data,
        )

        self._validate_order_format(order_data)

        return order_data

    def create_order(self, input_file):
        self.ensure_one()

        if input_file.state != 'draft':
            raise UserError(
                _(
                    'Cannot create an order from an input'
                    ' file that is not in a draft state'
                )
            )

        order_data = self.parse_order(input_file)

        order = self.env['integration.sale.order.factory'].create_order(
            self,
            order_data,
        )

        input_file.state = 'done'
        return order

    def integrationApiCreateOrders(self):
        self.ensure_one()

        input_files = self.env['sale.integration.input.file'].search([
            ('si_id', '=', self.id),
            ('state', '=', 'draft'),
        ])

        orders = self.env['sale.order']
        for input_file in input_files:
            orders += self.create_order(input_file)

        return orders

    @api.model
    def systray_get_integrations(self):
        integrations = self.search([
            ('state', '=', 'active'),
        ])

        result = []
        for integration in integrations:
            failed_jobs_count = self.env['queue.job'].sudo().search_count([
                ('model_name', '=', 'sale.integration'),
                ('func_string', 'like', f'{self._name}({integration.id},)'),
                ('state', '=', 'failed'),
                ('company_id', '=', integration.company_id.id)
            ])

            missing_mappings_count = 0
            for model_name in self.env:
                is_mapping_model = (
                    model_name.startswith('integration.')
                    and model_name.endswith('.mapping')
                )
                if not is_mapping_model:
                    continue

                mapping_model = self.env[model_name]
                internal_field_name, external_field_name = mapping_model._mapping_fields
                missing_mappings = mapping_model.search_count([
                    ('integration_id', '=', integration.id),
                    (internal_field_name, '=', False),
                    (external_field_name, '!=', False),
                ])

                missing_mappings_count += missing_mappings

            integration_stats = {
                'name': integration.name,
                'failed_jobs_count': failed_jobs_count,
                'missing_mappings_count': missing_mappings_count,
            }
            result.append(integration_stats)

        return result

    def _validate_order_format(self, order):
        address_schema = {
            'id': {'type': 'string'},
            'person_name': {'type': 'string'},
            'email': {'type': 'string'},
            'language': {'type': 'string', 'required': False},
            'person_id_number': {'type': 'string', 'required': False},
            'company_name': {'type': 'string', 'required': False},
            'company_reg_number': {'type': 'string', 'required': False},
            'street': {'type': 'string', 'required': False},
            'street2': {'type': 'string', 'required': False},
            'city': {'type': 'string', 'required': False},
            'country': {'type': 'string', 'required': False},
            'state': {'type': 'string', 'required': False},
            'zip': {'type': 'string', 'required': False},
            'phone': {'type': 'string', 'required': False},
            'mobile': {'type': 'string', 'required': False},
        }

        line_schema = {
            'id': {'type': 'string'},
            'product_id': {'type': 'string'},
            'product_uom_qty': {'type': 'number', 'required': False},
            'taxes': {
                'type': 'list',
                'schema': {'type': 'string'},
                'required': False,
            },
            'price_unit': {'type': 'number', 'required': False},
            'discount': {'type': 'number', 'required': False},
        }

        order_schema = {
            'id': {'type': 'string'},
            'ref': {'type': 'string'},
            'customer': {
                'type': 'dict',
                'schema': address_schema,
            },
            'shipping': {
                'type': 'dict',
                'schema': address_schema,
            },
            'billing': {
                'type': 'dict',
                'schema': address_schema,
            },
            'lines': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': line_schema
                },
            },
            'payment_method': {'type': 'string'},
            'carrier': {'type': 'string'},
            'shipping_cost': {'type': 'float'},
        }

        self._validate_by_schema(order, order_schema)

    def _validate_input_file_format(self, input_file):
        input_file_schema = {
            'id': {'type': 'string'},
            'data': {'type': 'dict'},
        }
        self._validate_by_schema(input_file, input_file_schema)

    def _validate_by_schema(self, data, schema):
        v = Validator(require_all=True, allow_unknown=True)
        valid = v.validate(data, schema)

        if not valid:
            raise Exception(v.errors)

    @api.model
    def _get_test_method(self):
        return [
            (method, method.replace('integrationApi', ''))
            for method in dir(self)
            if method.startswith('integrationApi') and callable(getattr(self, method))
        ]

    def test_job(self):
        method_name = self.test_method
        if not method_name:
            raise UserError(
                _(
                    'You should select test method in dropdown above, before clicking the button'
                )
            )
        test_method = getattr(self, method_name, None)
        if test_method:
            test_method()
        return True
