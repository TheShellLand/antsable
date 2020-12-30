"""
Handles credentials related stuff
"""

import xml.dom.minidom as xdm

import urllib
import framework.xml_dom_parser as xdp
import framework.rest as rest
import framework.log as log
import framework.ta_consts as c


_LOGGER = log.Logs().get_logger(c.ta_util)


class CredentialManager(object):
    """
    Credential related interfaces
    """

    _log_template = "Failed to %s user credential for %s, app=%s"

    def __init__(self, session_key, splunkd_uri="https://localhost:8089"):
        self._session_key = session_key
        self._splunkd_uri = splunkd_uri

    @staticmethod
    def get_session_key(username, password,
                        splunkd_uri="https://localhost:8089"):
        """
        Get session key by using login username and passwrod
        @return: session_key if successful, None if failed
        """

        eid = "".join((splunkd_uri, "/services/auth/login"))
        postargs = {
            "username": username,
            "password": password,
        }

        response, content = rest.splunkd_request(
            eid, None, method="POST", data=postargs)

        if response is None and content is None:
            return None

        xml_obj = xdm.parseString(content)
        session_nodes = xml_obj.getElementsByTagName("sessionKey")
        return session_nodes[0].firstChild.nodeValue

    def update(self, realm, user, password, app, owner="nobody"):
        """
        Update the password for a user and realm.
        @return: True if successful, False if failure
        """

        self.delete(realm, user, app, owner)
        return self.create(realm, user, password, app, owner)

    def create(self, realm, user, password, app, owner="nobody"):
        """
        Create a new stored credential.
        """

        payload = {
            "name": user,
            "password": password,
            "realm": realm,
        }

        endpoint = self._get_endpoint(realm, user, app, owner)
        resp, content = rest.splunkd_request(endpoint, self._session_key,
                                             method="POST", data=payload)
        if resp and resp.status in (200, 201):
            return True
        return False

    def delete(self, realm, user, app, owner="nobody"):
        """
        Delete the encrypted entry
        @return: True for success, False for failure
        """

        endpoint = self._get_endpoint(realm, user, app, owner)
        response, content = rest.splunkd_request(
            endpoint, self._session_key, method="DELETE")
        if response and response.status in (200, 201):
            return True
        return False

    def get_all_passwords(self):
        """
        @return: a list of dict when successful, None when failed.
        the dict at least contains
        {
            "realm": xxx,
            "username": yyy,
            "clear_password": zzz,
        }
        """

        endpoint = "{}/services/storage/passwords".format(self._splunkd_uri)
        response, content = rest.splunkd_request(
            endpoint, self._session_key, method="GET")
        if response and response.status in (200, 201) and content:
            return xdp.parse_conf_xml_dom(content)

    def get_clear_password(self, realm, user, app, owner="nobody"):
        """
        @return: clear password for specified realm and user
        """

        return self._get_credentials(realm, user, app, owner, "clear_password")

    def get_encrypted_password(self, realm, user, app, owner="nobody"):
        """
        @return: encyrpted password for specified realm and user
        """

        return self._get_credentials(realm, user, app, owner, "encr_password")

    def _get_credentials(self, realm, user, app, owner, prop):
        """
        @return: clear or encrypted password for specified realm, user
        """

        endpoint = self._get_endpoint(realm, user, app, owner)
        response, content = rest.splunkd_request(
            endpoint, self._session_key, method="GET")
        if response and response.status in (200, 201) and content:
            password = xdp.parse_conf_xml_dom(content)[0]
            return password[prop]
        return None

    @staticmethod
    def _build_name(realm, user):
        return urllib.quote(
            "".join((CredentialManager._escape_string(realm), ":",
                     CredentialManager._escape_string(user), ":")))

    @staticmethod
    def _escape_string(string_to_escape):
        """
        Splunk secure credential storage actually requires a custom style of
        escaped string where all the :'s are escaped by a single \.
        But don't escape the control : in the stanza name.
        """

        return string_to_escape.replace(":", "\\:").replace("/", "%2F")

    def _get_endpoint(self, realm, user, app, owner):
        if not owner:
            owner = "-"

        if not app:
            app = "-"

        realm_user = self._build_name(realm, user)
        rest_endpoint = "{}/servicesNS/{}/{}/storage/passwords/{}".format(
            self._splunkd_uri, owner, app, realm_user)
        return rest_endpoint
