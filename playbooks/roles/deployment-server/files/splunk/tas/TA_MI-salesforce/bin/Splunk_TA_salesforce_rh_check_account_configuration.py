"""
This module will be used to validate the if the account is valid or not
"""
import import_declare_test

import splunk.admin as admin
from solnlib import log
from solnlib import conf_manager


log.Logs.set_context()
logger = log.Logs().get_logger('splunk_ta_salesforce_rh_check_account_configuration')

"""
REST Endpoint to validate the if the account is valid or not
"""
class splunk_ta_salesforce_rh_check_account_configuration(admin.MConfigHandler):

    """
    This method checks which action is getting called and what parameters are required for the request.
    """
    def setup(self):
        if self.requestedAction == admin.ACTION_LIST:
            # Add required args in supported args
            self.supportedArgs.addReqArg('account_name')
        return

    """
    This handler is to validate the if the account is valid or not
    It takes 'account_name' as caller args and
    Returns the confInfo dict object in response.
    """
    def handleList(self, confInfo):
            logger.info('Entering handler to check account configuration')
            # Get args parameters from the request
            account_name = self.callerArgs.data['account_name'][0]

            cfm = conf_manager.ConfManager(self.getSessionKey(), "Splunk_TA_salesforce",
                                           realm="__REST_CREDENTIAL__#Splunk_TA_salesforce#configs/conf-splunk_ta_salesforce_account")
            conf = cfm.get_conf('splunk_ta_salesforce_account')
            account_stanza = conf.get(account_name, True)
            # Check if the account configuration is valid
            if 'auth_type' not in account_stanza:
                confInfo["account"]["isValid"] = "false"
            else:
                confInfo["account"]["isValid"] = "true"
            logger.info('Exiting handler to check account configuration')

if __name__ == "__main__":
    admin.init(splunk_ta_salesforce_rh_check_account_configuration, admin.CONTEXT_APP_AND_USER)