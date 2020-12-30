import splunk.admin as admin
from solnlib import conf_manager
from framework import rest
import framework.log as log
import traceback
import copy
import logging
from splunktaucclib.rest_handler.endpoint.validator import Validator
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)

APP_NAME = "Splunk_TA_snow"
_LOGGER = log.Logs().get_logger("main")

class GetSessionKey(admin.MConfigHandler):
    def __init__(self):
        self.session_key = self.getSessionKey()


class AccountValidation(Validator):
    '''
    Validate ServiceNow account details
    '''
    def __init__(self, *args, **kwargs):
        super(AccountValidation, self).__init__(*args, **kwargs)

    def getProxySettings(self, defaults):
        # Obtain proxy settings, if proxy has been configured, by reading splunk_ta_snow_settings.conf
        session_key_obj = GetSessionKey()
        session_key = session_key_obj.session_key

        settings_cfm = conf_manager.ConfManager(
                session_key,
                APP_NAME,
                realm="__REST_CREDENTIAL__#{}#configs/conf-splunk_ta_snow_settings".format(APP_NAME))


        splunk_ta_snow_settings_conf = settings_cfm.get_conf("splunk_ta_snow_settings").get_all()

        for key, value in splunk_ta_snow_settings_conf["proxy"].items():
            defaults[key] = value

        return defaults


    def validate(self, value, data):
        _LOGGER.info("Verifying username and password for ServiceNow instance {}.".format(data["url"]))
        defaults = self.getProxySettings(copy.deepcopy(data))
        url = defaults["url"]

        # Validate username and password for the account url entered 
        uri = ("{}/incident.do?JSONv2&sysparm_query="
               "sys_updated_on>=2000-01-01+00:00:00&sysparm_record_count=1")
        url = uri.format(url)
        http = rest.build_http_connection(
            defaults)
        try:
            resp, content = http.request(url)
        except Exception:
            msg = ("Unable to reach server at {}. Check configurations and network settings.".format(defaults["url"]))
            _LOGGER.error("Unable to reach ServiceNow instance at {0}. The reason for failure is={1}"
                          .format(defaults["url"], traceback.format_exc()))
            
            self.put_msg(msg, True)
            return False
        else:
            if resp.status not in (200, 201):
                msg = ("Failed to verify ServiceNow username and password, "
                       "code={} ({})").format(resp.status, resp.reason)
                _LOGGER.error("Failure occurred while verifying username and password. Response code={} ({})"
                              .format(resp.status, resp.reason))

                self.put_msg(msg, True)
                return False
            else:
                return True


class ProxyValidation(Validator):
    """
        Validate Proxy details provided
    """

    def __init__(self, *args, **kwargs):
        super(ProxyValidation, self).__init__(*args, **kwargs)

    def validate(self, value, data):
        _LOGGER.info("Verifying proxy details")

        username_val = data.get("proxy_username")
        password_val = data.get("proxy_password")

        # If password is specified, then username is required
        if password_val and not username_val:
            self.put_msg(
                'Username is required if password is specified', high_priority=True
            )
            return False
        # If username is specified, then password is required
        elif username_val and not password_val:
            self.put_msg(
                'Password is required if username is specified', high_priority=True
            )
            return False

        # If length of username is not satisfying the String length criteria
        if username_val:
            str_len = len(username_val)
            _min_len = 1
            _max_len = 50
            if str_len < _min_len or str_len > _max_len:
                msg = 'String length of username should be between %(min_len)s and %(max_len)s' % {
                    'min_len': _min_len,
                    'max_len': _max_len
                }
                self.put_msg(msg, high_priority=True)
                return False

        return True
