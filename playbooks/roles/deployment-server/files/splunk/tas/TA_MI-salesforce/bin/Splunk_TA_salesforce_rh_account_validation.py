import splunk.admin as admin
import httplib2_helper
from httplib2 import Http, ProxyInfo, socks
import urllib
from solnlib import log
from solnlib import conf_manager
from solnlib.utils import is_true
import traceback
import copy
from cloudconnectlib.core.ext import regex_search
from splunktaucclib.rest_handler.endpoint.validator import Validator

APP_NAME = "Splunk_TA_salesforce"
_FAULT_STRING_REGEX = '\<faultstring\>(?P<faultstring>.*)\<\/faultstring\>'
_FAULT_CODE_REGEX = '\<faultcode\>sf:(?P<faultcode>.*)\<\/faultcode\>'
_DEFAULT_ERROR = "Login Salesforce failed. Please check your network environment and credentials."

log.Logs.set_context()
logger = log.Logs().get_logger('ta_salesforce_basic_account_validation')

# Map for available proxy type
_PROXY_TYPE_MAP = {
    'http': socks.PROXY_TYPE_HTTP,
    'socks4': socks.PROXY_TYPE_SOCKS4,
    'socks5': socks.PROXY_TYPE_SOCKS5,
}

class GetSessionKey(admin.MConfigHandler):
    def __init__(self):
        self.session_key = self.getSessionKey()

class AccountValidation(Validator):

    def __init__(self, *args, **kwargs):
        super(AccountValidation, self).__init__(*args, **kwargs)

    def getProxyDetails(self):
        session_key_obj = GetSessionKey()
        session_key = session_key_obj.session_key        
        # Create confmanger object for the app with realm
        cfm = conf_manager.ConfManager(session_key, APP_NAME, realm="__REST_CREDENTIAL__#Splunk_TA_salesforce#configs/conf-splunk_ta_salesforce_settings")
        # Get Conf object of apps settings
        conf = cfm.get_conf('splunk_ta_salesforce_settings')
        # Get proxy stanza from the settings
        proxy_config = conf.get("proxy", True)
        if not proxy_config or not is_true(proxy_config.get('proxy_enabled')):
            logger.info('Proxy is not enabled')
            return None

        url = proxy_config.get('proxy_url')
        port = proxy_config.get('proxy_port')

        if url or port:
            if not url:
                raise ValueError('Proxy "url" must not be empty')
            if not self.is_valid_port(port):
                raise ValueError(
                    'Proxy "port" must be in range [1,65535]: %s' % port
                )

        user = proxy_config.get('proxy_username')
        password = proxy_config.get('proxy_password')

        if not all((user, password)):
            logger.info('No proxy credentials found')
            user, password = None, None

        proxy_type = proxy_config.get('proxy_type')
        proxy_type = proxy_type.lower() if proxy_type else 'http'

        if proxy_type in _PROXY_TYPE_MAP:
            ptv = _PROXY_TYPE_MAP[proxy_type]
        elif proxy_type in _PROXY_TYPE_MAP.values():
            ptv = proxy_type
        else:
            ptv = socks.PROXY_TYPE_HTTP
            logger.info('Proxy type not found, setting it to "HTTP"')

        rdns = is_true(proxy_config.get('proxy_rdns'))

        proxy_info = ProxyInfo(
            proxy_host=url,
            proxy_port=int(port),
            proxy_type=ptv,
            proxy_user=user,
            proxy_pass=password,
            proxy_rdns=rdns
        )
        return proxy_info

    """
    Method to check if the given port is valid or not
    :param port: port number to be validated
    :type port: ``int``
    """

    def is_valid_port(self, port):
        try:
            return 0 < int(port) <= 65535
        except ValueError:
            return False

    def validate(self, value, data):

        ## Validate Salesforce Account credentials        
        logger.info("Validating salesforce account credentials")

        ## Get Proxy configurations from splunk_ta_salesforce_settings.conf
        proxy_info = self.getProxyDetails()

        defaults = copy.deepcopy(data)
        http = Http(proxy_info=proxy_info)
        rq_body = ('<?xml version="1.0" encoding="utf-8" ?>'
            '<env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            ' xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">'
            '<env:Body>'
            '<n1:login xmlns:n1="urn:partner.soap.sforce.com">'
            '<n1:username>'+defaults['username']+'</n1:username>'
            '<n1:password><![CDATA['+defaults['password']+']]>'+defaults['token']+'</n1:password>'
            '</n1:login></env:Body>'
            '</env:Envelope>')
        
        header = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'login'
        }

        try:
            account_endpoint = defaults["endpoint"]
            account_sfdc_api_version = defaults["sfdc_api_version"]
            logger.info("Invoking request to [https://"+account_endpoint+"/services/Soap/u/"+account_sfdc_api_version+"/] using [POST] method")
            resp, content = http.request("https://"+account_endpoint+"/services/Soap/u/"+account_sfdc_api_version+"/", 
                        method="POST", 
                        headers=header,
                        body=rq_body)
            content = content.decode()
        except Exception:
            msg = (
                "Some error occured while validating credentials for salesforce username {}. Check ta_salesforce_basic_account_validation.log for more details.".format(
                    defaults["username"]))
            logger.error(
                "While validating credentials for salesforce username %s, some error occured. Check your network connection and try again.\nreason=%s",
                defaults["username"], traceback.format_exc())
            self.put_msg(msg, True)
            return False

        if int(resp['status']) == 200:
            logger.info("Successfully validated salesforce account credentials for username %s", defaults["username"])
            return True
        else:
            error = regex_search(_FAULT_CODE_REGEX, content) if content else {}
            fault_code = error.get('faultcode', _DEFAULT_ERROR)
            error_description = regex_search(_FAULT_STRING_REGEX, content) if content else {}
            fault_string = error_description.get('faultstring', _DEFAULT_ERROR)
            
            code_msg_tbl = {
                'INVALID_LOGIN': "Invalid username, password, security token; or user locked out.",
                'LOGIN_MUST_USE_SECURITY_TOKEN': "When accessing Salesforce, either via a desktop client or the API from outside of your company's trusted networks, you must add a security token to your password to log in.",
                'REQUEST_LIMIT_EXCEEDED': "Login Failed, TotalRequests Limit exceeded."
            }
                        
            fault_msg = code_msg_tbl.get(fault_code, _DEFAULT_ERROR)
            msg = (fault_msg)
            logger.error("Login failed for salesforce account %s with reason %s", defaults["username"], fault_string)
            self.put_msg(msg, True)
            return False
