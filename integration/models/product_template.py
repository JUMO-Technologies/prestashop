# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from .template_converter import TemplateConverter
import logging
from ..tools import _guess_mimetype

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'integration.model.mixin']
    _description = 'Product Template'

    default_public_categ_id = fields.Many2one(
        comodel_name='product.public.category',
        string='Default Category',
    )

    public_categ_ids = fields.Many2many(
        comodel_name='product.public.category',
        relation='product_public_category_product_template_rel',
        string='Website Product Category',
    )

    product_template_image_ids = fields.One2many(
        comodel_name='product.image',
        inverse_name='product_tmpl_id',
        string='Extra Product Media',
        copy=True,
    )

    website_product_name = fields.Char(
        string='Product Name',
        translate=True,
        help='Sometimes it is required to define separate field with beautiful product name. '
             'And standard field to use for technical name in Odoo WMS (usable for Warehouses). '
             'If current field is not empty it will be used for sending to '
             'e-Commerce System instead of standard field.'
    )

    website_description = fields.Html(
        string='Website Description',
        sanitize=False,
        translate=True,
    )

    website_short_description = fields.Html(
        string='Short Description',
        sanitize=False,
        translate=True,
    )

    website_seo_metatitle = fields.Char(
        string='Meta title',
        translate=True,
    )

    website_seo_description = fields.Char(
        string='Meta description',
        translate=True,
    )

    @api.model
    def _get_sale_integrations(self):
        active_integrations = self.env['sale.integration'].search([('state', '=', 'active')])
        if active_integrations:
            return active_integrations.ids
        return []

    integration_ids = fields.Many2many(
        'sale.integration',
        'sale_integration_product',
        'product_id',
        'sale_integration_id',
        'Sales Integrations',
        domain=[('state', '=', 'active')],
        help='Allow to select which channel this product should be synchronized to. '
             'By default it syncs to all.',
        default=lambda self: self._get_sale_integrations(),
        )

    @api.model
    def create(self, vals_list):
        # We need to avoid calling export separately
        # from product.template and product.product
        ctx = dict(self.env.context, from_product_template=True, from_product_create=True)
        from_product_product = ctx.pop('from_product_product', False)

        templates = super(ProductTemplate, self.with_context(ctx)).create(vals_list)

        if not from_product_product:
            templates.trigger_export(export_images=self._need_export_images(vals_list))

        return templates

    def write(self, vals):
        # We need to avoid calling export separately
        # from product.template and product.product
        ctx = dict(self.env.context, from_product_template=True)
        from_product_product = ctx.pop('from_product_product', False)

        result = super(ProductTemplate, self.with_context(ctx)).write(vals)

        if not from_product_product:
            self.trigger_export(export_images=self._need_export_images(vals))

        return result

    @api.model
    def _need_export_images(self, vals_list):
        return self._check_fields_changed(
            [
                'image_1920',
                'product_template_image_ids',
            ],
            vals_list
        )

    def trigger_export(self, export_images=False):
        # We need to allow skipping exporting in some cases
        # hence adding context here in generic action
        if self.env.context.get('skip_product_export'):
            return

        # If we are creating a new product than we always export images
        # We need this because when new product is created, than system is calling create()
        # and write() methods on product template. And trigger_export() is called twice with
        # export_images=False and export_images=True. That causing duplicated job to be created
        # As result duplicated products are created on e-Commerce system!
        if self.env.context.get('from_product_create'):
            export_images = True

        # identity_key contains export_images flag because we want to be sure
        # that we didn't skip exporting images if there is job with export_images=False
        for template in self:
            integrations = self.env['sale.integration'].get_integrations(
                'export_template',
                template.company_id,
            )

            for integration in integrations:
                key = 'export_template_%s_%s_%s' % (
                    integration.id, template.id, export_images
                )

                if integration.id in template.integration_ids.ids:
                    integration.with_delay(identity_key=key).export_template(
                        template, export_images=export_images
                    )

    def to_export_format(self, integration):
        self.ensure_one()
        contexted_template = self.with_context(active_test=False)
        return TemplateConverter(integration).convert(contexted_template)

    def to_images_export_format(self, integration):
        self.ensure_one()

        template_images_data = self._template_or_variant_to_images_export_format(
            self,
            integration,
        )

        products_images_data = []
        for product in self.product_variant_ids:
            image_data = self._template_or_variant_to_images_export_format(
                product,
                integration,
            )
            products_images_data.append(image_data)

        result = {
            'template': template_images_data,
            'products': products_images_data,
        }
        return result

    @api.model
    def _template_or_variant_to_images_export_format(self, record, integration):
        if record._name == 'product.template':
            extra_images = record.product_template_image_ids
            default_image_field = 'image_1920'
        else:
            extra_images = record.product_variant_image_ids
            default_image_field = 'image_variant_1920'

        default_image_data = record[default_image_field]
        if default_image_data:
            default_image = {
                'data': default_image_data,
                'mimetype': _guess_mimetype(default_image_data),
            }
        else:
            default_image = None

        extra_images_data = []
        for extra_image in extra_images:
            extra_image_data = {
                'data': extra_image.image_1920,
                'mimetype': _guess_mimetype(extra_image.image_1920)
            }
            extra_images_data.append(extra_image_data)

        images_data = {
            'id': record.to_external(integration),
            'default': default_image,
            'extra': extra_images_data,
        }

        return images_data

    # -------- Converter Specific Methods ---------
    def get_integration_name(self, integration):
        self.ensure_one()
        name_field = 'name'
        if self.website_product_name:
            name_field = 'website_product_name'
        return integration.convert_translated_field_to_integration_format(
            self, name_field
        )

    def get_default_category(self, integration):
        self.ensure_one()
        default_category = self.default_public_categ_id
        if default_category:
            return default_category.to_external_or_export(integration)
        else:
            return None

    def get_categories(self, integration):
        return [
            x.to_external_or_export(integration)
            for x in self.public_categ_ids
        ]

    def get_taxes(self, integration):
        result = []

        integration_company_taxes = self.taxes_id.filtered(
            lambda x: x.company_id == integration.company_id
        )
        for tax in integration_company_taxes:
            result.append({
                'tax_id': tax.to_external(integration),
                'tax_group_id': tax.tax_group_id.to_external(integration),
            })

        return result
