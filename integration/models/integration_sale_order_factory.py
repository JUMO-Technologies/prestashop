# See LICENSE file for full copyright and licensing details.

from ..exceptions import NotMapped
from odoo import models, api


class IntegrationSaleOrderFactory(models.AbstractModel):
    _name = 'integration.sale.order.factory'
    _description = 'Integration Sale Order Factory'

    @api.model
    def get_not_mapped(self, integration, order_data):
        not_mapped = []

        payment_method_external_code = order_data['payment_method']
        try:
            self.env['sale.order.payment.method'].from_external(
                integration,
                payment_method_external_code,
            )
        except NotMapped as e:
            # Payment methods mapping should be created dynamically
            # It should not cause issues with order validation
            integration.integrationApiImportPaymentMethods()

        carrier_external_code = order_data['carrier']
        try:
            self.env['delivery.carrier'].from_external(
                integration,
                carrier_external_code,
            )
        except NotMapped as e:
            not_mapped.append(e.value)

        for address_type in ('customer', 'billing', 'shipping'):
            address_data = order_data[address_type]

            country_external_code = address_data.get('country')
            if country_external_code:
                try:
                    self.env['res.country'].from_external(
                        integration,
                        country_external_code,
                    )
                except NotMapped as e:
                    not_mapped.append(e.value)

            state_external_code = address_data.get('state')
            if state_external_code:
                try:
                    self.env['res.country.state'].from_external(
                        integration,
                        state_external_code,
                    )
                except NotMapped as e:
                    not_mapped.append(e.value)

        for line in order_data['lines']:
            external_code = line['product_id']
            try:
                self.env['product.product'].from_external(
                    integration,
                    external_code,
                )
            except NotMapped as e:
                not_mapped.append(e.value)

            taxes = line.get('taxes', [])
            for tax_external_code in taxes:
                try:
                    self.env['account.tax'].from_external(
                        integration,
                        tax_external_code,
                    )
                except NotMapped as e:
                    not_mapped.append(e.value)

        return not_mapped

    @api.model
    def create_order(self, integration, order_data):
        order = self.env['integration.sale.order.mapping'].search([
            ('integration_id', '=', integration.id),
            ('external_id.code', '=', order_data['id']),
        ]).odoo_id
        if not order:
            order = self._create_order(integration, order_data)
            order.create_mapping(integration, order_data['id'])
            self._post_create(integration, order)
        return order

    @api.model
    def _create_order(self, integration, order_data):
        order_vals = self._prepare_order_vals(integration, order_data)

        order = self.env['sale.order'].create(order_vals)

        if integration.order_name_ref:
            order.name += '/%s' % integration.order_name_ref
        order.name += '/%s' % order_data['ref']

        if integration.default_sales_team_id:
            order.team_id = integration.default_sales_team_id.id

        carrier = self.env['delivery.carrier'].from_external(
            integration, order_data['carrier']
        )
        order.set_delivery_line(carrier, order_data['shipping_cost'])
        return order

    @api.model
    def _prepare_order_vals(self, integration, order_data):
        partner, shipping, billing = self._create_customer(integration, order_data)

        payment_method = self.env['sale.order.payment.method'].from_external(
            integration, order_data['payment_method']
        )

        delivery_notes_field_name = integration.so_delivery_note_field.name

        order_line = []
        for line in order_data['lines']:
            order_line.append((0, 0, self._prepare_order_line_vals(integration, line)))

        return {
            'integration_id': integration.id,
            'partner_id': partner.id,
            'partner_shipping_id': shipping.id,
            'partner_invoice_id': billing.id,
            'order_line': order_line,
            'payment_method_id': payment_method.id,
            delivery_notes_field_name: order_data['delivery_notes'],
        }

    @api.model
    def _create_customer(self, integration, order_data):
        customer = self._create_partner(integration, order_data['customer'])
        customer.customer_rank = 1

        shipping = self._create_partner(integration, order_data['shipping'], 'delivery')

        billing = self._create_partner(integration, order_data['billing'], 'invoice')

        return customer, shipping, billing

    @api.model
    def _create_partner(self, integration, partner_data, address_type=None):
        try:
            partner = self.env['res.partner'].from_external(
                integration, partner_data['id']
            )
        except NotMapped:
            partner = None

        if partner_data.get('country'):
            country = self.env['res.country'].from_external(
                integration, partner_data.get('country')
            )
        else:
            country = self.env['res.country']

        if partner_data.get('state'):
            state = self.env['res.country.state'].from_external(
                integration, partner_data.get('state')
            )
        else:
            state = self.env['res.country.state']

        vals = {
            'name': partner_data['person_name'],
            'street': partner_data.get('street'),
            'street2': partner_data.get('street2'),
            'city': partner_data.get('city'),
            'country_id': country.id,
            'state_id': state.id,
            'zip': partner_data.get('zip'),
            'email': partner_data.get('email'),
            'phone': partner_data.get('phone'),
            'mobile': partner_data.get('mobile'),
            'integration_id': integration.id,
        }

        if partner_data.get('language'):
            language = self.env['res.lang'].from_external(
                integration, partner_data.get('language')
            )
            if language:
                vals.update({
                    'lang': language.code,
                })

        person_id_field = integration.customer_personal_id_field
        if person_id_field:
            vals.update({
                person_id_field.name: partner_data.get('person_id_number'),
            })

        if address_type:
            vals['type'] = address_type

        # Adding Company Specific fields
        if partner_data.get('company_name'):
            vals.update({
                'company_name': partner_data.get('company_name'),
            })

        company_vat_field = integration.customer_company_vat_field
        if company_vat_field and partner_data.get('company_reg_number'):
            vals.update({
                company_vat_field.name: partner_data.get('company_reg_number'),
            })

        if partner:
            partner.write(vals)
        else:
            partner = self.env['res.partner'].create(vals)
            partner.create_mapping(integration, partner_data['id'])

        return partner

    @api.model
    def _prepare_order_line_vals(self, integration, line):
        product = self.env['product.product'].from_external(
            integration,
            line['product_id'],
        )

        vals = {
            'integration_external_id': line['id'],
            'product_id': product.id,
        }

        if 'product_uom_qty' in line:
            vals.update(product_uom_qty=line['product_uom_qty'])

        if 'price_unit' in line:
            vals.update(price_unit=line['price_unit'])

        if 'taxes' in line:
            taxes = self.env['account.tax'].browse()
            for tax_id in line['taxes']:
                taxes |= self.env['account.tax'].from_external(
                    integration, tax_id
                )
            vals.update(tax_id=[(6, 0, taxes.ids)])

        if 'discount' in line:
            vals.update(discount=line['discount'])

        return vals

    @api.model
    def _post_create(self, integration, order):
        if not integration.sale_order_auto_confirm:
            return

        try:
            with self.env.cr.savepoint():
                order.action_confirm()
        except Exception as e:
            exception_msg = str(e)
            msg = f'Quotation wasn\'t confirmed because of Exception: {exception_msg}'
            order.message_post(body=msg)
