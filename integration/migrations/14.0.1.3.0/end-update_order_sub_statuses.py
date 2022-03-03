from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Updates Integration fields for Delivery Note and Products
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    integrations = env['sale.integration'].search([])

    sub_status_mapping_model = env['integration.sale.order.sub.status.mapping']

    for integration in integrations:
        sub_statuses = env['integration.sale.order.sub.status.external']\
            .search([('integration_id', '=', integration.id)])
        for sub_status in sub_statuses:
            existing_mapping = sub_status_mapping_model.\
                search([('external_id', '=', sub_status.id)])
            # Step 1: If there is existing full mapping, than we should just fix Odoo object
            if existing_mapping and existing_mapping.odoo_id:
                odoo_sub_status = existing_mapping.odoo_id
                odoo_sub_status.integration_id = integration.id
                continue

            # Step 2: We should create new odoo sub status
            odoo_model = env['sale.order.sub.status']
            create_vals = {
                'code': sub_status.external_reference,
                'integration_id': sub_status.integration_id.id,
                'name': sub_status.name,
            }
            odoo_sub_status = odoo_model.create(create_vals)

            # Step 3. If there is mapping with not linked Odoo object - than we just link it
            if existing_mapping:
                existing_mapping.odoo_id = odoo_sub_status.id
                continue
            create_vals = {
                'odoo_id': odoo_sub_status.id,
                'integration_id': sub_status.integration_id.id,
                'external_id': sub_status.id,
            }
            sub_status_mapping_model.create(create_vals)
