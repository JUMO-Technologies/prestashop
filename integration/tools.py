import base64
from odoo.tools.mimetypes import guess_mimetype


def _guess_mimetype(data):
    if not data:
        return None

    raw = base64.b64decode(data)
    mimetype = guess_mimetype(raw)
    return mimetype
