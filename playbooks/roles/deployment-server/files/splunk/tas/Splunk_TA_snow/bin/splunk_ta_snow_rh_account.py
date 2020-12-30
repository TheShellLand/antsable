
import import_declare_test

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
import logging
from splunk_ta_snow_account_validation import AccountValidation

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'url',
        required=True,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""https://\S*""", 
        )
    ), 
    field.RestField(
        'username',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'password',
        required=True,
        encrypted=True,
        default=None,
        validator=AccountValidation()
    ), 
    field.RestField(
        'record_count',
        required=False,
        encrypted=False,
        default=1000,
        validator=validator.Pattern(
            regex=r"""^[0-9]*$""", 
        )
    ),
    field.RestField(
        'disable_ssl_certificate_validation',
        required=False,
        encrypted=False,
        default=0,
        validator=None
    )
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    'splunk_ta_snow_account',
    model,
    config_name='account'
)


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
