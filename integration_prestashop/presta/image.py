#  See LICENSE file for full copyright and licensing details.

import base64

from .base_model import BaseModel


class Image(BaseModel):

    _product_id = None

    def create(self, name, data):
        result = self._client.add('images/products/' + str(self._product_id), files=[
            ('image', name, base64.b64decode(data))
        ], options=self._id_group_shop_options)
        return result['prestashop']['image']['id']

    def delete(self):
        product_images_full_url = (
            self._client._api_url
            + 'images/products/'
            + str(self._product_id)
        )

        delete_url = product_images_full_url + '/' + str(self.id)
        if self._id_group_shop:
            delete_url += '?id_group_shop=%s' % self._id_group_shop

        return self._client.delete_with_url(delete_url)
