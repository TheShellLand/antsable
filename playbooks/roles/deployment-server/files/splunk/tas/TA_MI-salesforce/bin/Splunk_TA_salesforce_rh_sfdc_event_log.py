
import import_declare_test

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from solnlib import conf_manager
from solnlib.splunkenv import make_splunkhome_path
import shutil
import os
import hashlib
import logging

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        'interval',
        required=True,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""^\-[1-9]\d*$|^\d*$""", 
        )
    ), 
    field.RestField(
        'index',
        required=True,
        encrypted=False,
        default='default',
        validator=validator.String(
            max_len=80, 
            min_len=1, 
        )
    ), 
    field.RestField(
        'account',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'start_date',
        required=False,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}z)?$""", 
        )
    ),
    field.RestField(
        'use_existing_checkpoint',
        required=False,
        encrypted=False,
        default='no',
    ),
    field.RestField(
        'disabled',
        required=False,
        validator=None
    ),
    field.RestField(
        'token',
        required=False,
        validator=None
    ),
    field.RestField(
        'endpoint',
        required=False,
        validator=None
    ),
    field.RestField(
        'monitoring_interval',
        required=True,
        validator=None
    )

]
model = RestModel(fields, name=None)



endpoint = DataInputModel(
    'sfdc_event_log',
    model,
)

class SfdcEventLogExternalHandler(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)
        try:
            cfm = conf_manager.ConfManager(self.getSessionKey(), "Splunk_TA_salesforce",
                                       realm="__REST_CREDENTIAL__#Splunk_TA_salesforce#configs/conf-splunk_ta_salesforce_account")
            # Get Conf object of apps settings
            conf = cfm.get_conf('splunk_ta_salesforce_account')
            # Get account stanza from the settings
            account_configs = conf.get_all()
            for inputStanzaKey, inputStanzaValue in list(confInfo.items()):
                if 'account' in inputStanzaValue and 'auth_type' not in list(account_configs[inputStanzaValue["account"]].keys()):
                    inputStanzaValue['invalid'] = "true"
        except conf_manager.ConfManagerException:
            # For fresh addon splunk_ta_salesforce_account will not exist so handling that exception
            pass

    def handleEdit(self, confInfo):
        disabled = self.payload.get('disabled')
        # remove checkpoint if user want to reset checkpoint in edit mode
        if disabled is None and self.payload.get('use_existing_checkpoint') == 'no':
            self.removeCheckpoint()
        if 'use_existing_checkpoint' in self.payload:
            del self.payload['use_existing_checkpoint']
        AdminExternalHandler.handleEdit(self, confInfo)

    def handleCreate(self, confInfo):
        # remove checkpoint if user want to reset checkpoint in create mode
        if self.payload.get('use_existing_checkpoint') == 'no':
            self.removeCheckpoint()
        if 'use_existing_checkpoint' in self.payload:
            del self.payload['use_existing_checkpoint']
        AdminExternalHandler.handleCreate(self, confInfo)

    def removeCheckpoint(self):
        # Get checkpoint directory
        hashed_folder = hashlib.sha256(str(self.callerArgs.id).encode("utf-8")).hexdigest()
        checkpoint_dir = make_splunkhome_path(['var', 'lib', 'splunk', 'modinputs', 'sfdc_event_log',
                                      hashed_folder])
        # If the directory exists remove checkpoint
        if os.path.exists(checkpoint_dir):
            shutil.rmtree(checkpoint_dir)

if __name__ == '__main__':
    logging.getLogger().addHandler(logging.NullHandler())
    admin_external.handle(
        endpoint,
        handler=SfdcEventLogExternalHandler,
    )
