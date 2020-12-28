"""
This module will be used to validate the if the checkpoint exist for given input or not
"""
import import_declare_test

import splunk.admin as admin
from solnlib import log
from solnlib import conf_manager
import os
import hashlib
import json
from jsonschema import validate
import shutil

log.Logs.set_context()
logger = log.Logs().get_logger('splunk_ta_salesforce_rh_check_input_checkpoint')

"""
REST Endpoint to validate the if the checkpoint exist for given input or not
"""
class splunk_ta_salesforce_rh_check_input_checkpoint(admin.MConfigHandler):

    """
    This method checks which action is getting called and what parameters are required for the request.
    """
    def setup(self):
        if self.requestedAction == admin.ACTION_LIST:
            # Add required args in supported args
            self.supportedArgs.addReqArg('input_name')
            self.supportedArgs.addReqArg('service_name')
        return

    """
    This handler is to validate the checkpoint exist for given input or not
    It takes 'input_name' as caller args and
    Returns the confInfo dict object in response.
    """
    def handleList(self, confInfo):
            # Get args parameters from the request
            input_name = self.callerArgs.data['input_name'][0]
            service_name = self.callerArgs.data['service_name'][0]
            logger.info('Entering handler to check checkpoint for input %s', input_name)
            splunk_home = os.path.abspath(os.path.join(os.getcwd(), os.environ.get('SPLUNK_HOME', '')))
            checkpoint_hash_name = hashlib.sha256(input_name.encode("utf-8")).hexdigest()
            checkpoint_dir = os.path.join(splunk_home, 'var', 'lib', 'splunk', 'modinputs', service_name, checkpoint_hash_name)
            checkpoint_file = os.path.join(splunk_home, 'var', 'lib', 'splunk', 'modinputs', service_name, checkpoint_hash_name ,checkpoint_hash_name)

            # Check if the checkpoint exist and not corrupted
            schema_eventlog = { "type": "object","required": ["namespaces","data"],"properties": {"namespaces": { "type": "array","items": {"type": "string"}},
                                "data": {"type": "object","required": ["records","start_date_config","records_on_start_date","start_date"],"properties": {"records": {"type": "array"},
                                "start_date_config": {"type": "string"},"records_on_start_date": {"type": "array"},"start_date": {"type": "string"}}}}}

            schema_objectlog = { "type": "object","required": ["namespaces","data"],"properties": {"namespaces": {"type": "array","items": {"type": "string"}},
                                 "data": {"type": "object","required": ["start_date","is_greater_than","start_date_config"],"properties": {"start_date": {"type": "string"},
                                 "is_greater_than": {"type": "string","start_date_config": {"type": "string"}}}}}}
            try:
                if os.path.exists(checkpoint_dir):
                    with open(checkpoint_file, 'r') as chk_file:
                        chk_content = json.load(chk_file)
                        if service_name == "sfdc_object":
                            validate(instance=chk_content, schema=schema_objectlog)
                        elif service_name == "sfdc_event_log":
                            validate(instance=chk_content, schema=schema_eventlog)

                    confInfo["account"]["isExist"] = "true"
                else:
                    confInfo["account"]["isExist"] = "false"

            except Exception:
                logger.error("Corrupted checkpoint is found hence removing it.")
                shutil.rmtree(checkpoint_dir)
                confInfo["account"]["isExist"] = "false"
            logger.info('Exiting handler to check checkpoint for input with status %s', confInfo["account"]["isExist"])

if __name__ == "__main__":
    admin.init(splunk_ta_salesforce_rh_check_input_checkpoint, admin.CONTEXT_APP_AND_USER)
