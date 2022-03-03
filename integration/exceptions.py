# See LICENSE file for full copyright and licensing details.


class NotMapped(Exception):

    def __init__(self, msg, value=None):
        super(NotMapped, self).__init__(msg)
        self.value = value


class NotMappedValue:

    def __init__(self, model_name, external_code):
        self.model_name = model_name
        self.external_code = external_code


class NoReferenceFieldDefined(Exception):

    def __init__(self, msg, object_name=None):
        super(NoReferenceFieldDefined, self).__init__(msg)
        self.object_name = object_name
