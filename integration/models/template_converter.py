# See LICENSE file for full copyright and licensing details.


class TemplateConverter:

    def __init__(self, integration):
        self._integration = integration
        self.env = integration.env

    def convert(self, template):
        external_id = template.try_to_external(self._integration)
        result = {
            'id': template.id,
            'external_id': external_id,
            'type': template.type,
            'kits': self._get_kits(template),
            'products': [
                x.to_export_format(self._integration)
                for x in template.product_variant_ids
            ],
        }
        search_domain = [
            ('odoo_model_id', '=', self.env.ref('product.model_product_template').id),
            ('integration_id', '=', self._integration.id),
        ]
        if external_id:
            search_domain += [('send_on_update', '=', True)]
        for field in self.env['product.ecommerce.field.mapping'].\
                search(search_domain).mapped('ecommerce_field_id'):
            result[field.technical_name] = self._integration.calculate_field_value(template, field)
        return result

    def convert_for_update(self, template):
        self.convert(template, True)

    def _get_kits(self, template):
        kits = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', template.id),
            ('type', '=', 'phantom'),
            ('company_id', 'in', (self._integration.company_id.id, False)),
        ])
        kits_data = []
        for kit in kits:
            components = []
            for bom_line in kit.bom_line_ids:
                components.append({
                    'product_id': bom_line.product_id.to_external(self._integration),
                    'qty': bom_line.product_qty,
                })

            kits_data.append({
                'components': components,
            })

        return kits_data
