import import_declare_test
from future import standard_library
standard_library.install_aliases()
import snow_incident_base as sib
from framework import rest
import splunk.Intersplunk as si
import sys
import re
import traceback
import json

class SnowIncidentAlert(sib.SnowIncidentBase):

    def __init__(self):

        # set session key
        self.sessionkey = self._set_session_key()

        # read input
        self.res = self._set_events()
        # no events found
        if not self.res:
            exit(0)

        # get account name
        for event in self.res:
            self.account = event.get("account", None)
            if self.account:
                break
        if not self.account:
            self._handle_error('Field "account" is required by ServiceNow '
                               'for creating incidents')
        
        super(SnowIncidentAlert, self).__init__()

    def _get_events(self):
        # keeps only the first element from list of 'n' results
        # hence it creates only one incident on the snow instance
        self.res = [self.res[0]]
        return self.res

    def _set_events(self):
        """
            Fetch inputs from the search results
        """
        return si.readResults(sys.stdin, None, True)

    def _set_session_key(self):
        """
            When called as custom search script, splunkd feeds the following
            to the script as a single line
            'authString:<auth><userId>admin</userId><username>admin</username>\
                <authToken>31619c06960f6deaa49c769c9c68ffb6</authToken></auth>'
        """
        import urllib.parse
        session_key = sys.stdin.readline()
        m = re.search("authToken>(.+)</authToken", session_key)
        if m:
            session_key = m.group(1)
        session_key = urllib.parse.unquote(session_key.encode("ascii").decode("ascii"))
        session_key = session_key.encode().decode("utf-8")
        return session_key

    def _get_session_key(self):
        return self.sessionkey

    def _handle_error(self, msg="Failed to create ticket."):
        si.parseError(msg)
    
    def _get_result(self, resp):

        result = {
            "Incident Number": "",
            "Created": resp.get("sys_created_on"),
            "Priority": resp.get("priority"),
            "Updated": resp.get("sys_updated_on"),
            "Short Description": resp.get("short_description"),
            "Category": resp.get("category"),
            "Incident Link": resp.get("sys_target_sys_id", {}).get("link"),
            "Contact Type": resp.get("contact_type"),
            "ciIdentifier": resp.get("configuration_item"),
            "State": resp.get("state"),
            "Sys Id": resp.get("sys_id"),
            "Correlation ID": resp.get("correlation_id"),
            "Splunk URL": resp.get("splunk_url"),
            "Incident Creation": resp.get("sys_import_state")
        }

        headers = {"Content-type": "application/json", "Accept":"application/json"}
        snow_url = resp.get("sys_target_sys_id", {}).get("link")
        http = rest.build_http_connection(self.snow_account)
        try:
            response, content = http.request(snow_url, "GET", None, headers)
        except Exception:
            self.logger.error(traceback.format_exc())
        else:
            if response.status in (200, 201):
                # getting the incident information from the Incident table.
                # In case if it fails to get the information from the incident table 
                # it will fetch the fields values of intermediate table
                resp = self._get_resp_record(content)
                self.logger.debug("Response from Incident table incident: %s", resp)
                result["Incident Number"] = resp.get("number", result.get("Incident Number"))
                result["Incident Link"] = "{}incident.do?sysparm_query=number={}".format(self.snow_account["url"], resp.get("number"))
                result["Sys Id"] = resp.get("sys_id", result.get("Sys Id"))
                result["Created"] = resp.get("sys_created_on", result.get("Created"))
                result["Priority"] = resp.get("priority", result.get("Priority"))
                result["State"] = resp.get("state", result.get("State"))
                result["Updated"] = resp.get("sys_updated_on", result.get("Updated"))
                result["Category"] = resp.get("category", result.get("Category"))
                result["Contact Type"] = resp.get("contact_type", result.get("Contact Type"))
                result["Short Description"] = resp.get("short_description", result.get("Short Description"))
                result["ciIdentifier"] = resp.get("configuration_item", result.get("ciIdentifier"))
                result["Splunk URL"] = resp.get("splunk_url", result.get("Splunk URL"))
                result["Incident Creation"] = resp.get("sys_import_state", result.get("Incident Creation"))
            else:
                self.logger.error("Failed to get incident information. Return status is {0}.".format(response.status))
                self.logger.error(traceback.format_exc())

        return result

    def _handle_response(self, response, content):
        if response.status in (200, 201):
            resp = self._get_resp_record(content)
            if (resp and resp.get("sys_row_error")):
                headers = {"Content-type": "application/json", "Accept":"application/json"}
                error_url = resp["sys_row_error"]["link"]
                http = rest.build_http_connection(self.snow_account)
                try:
                    error_response, error_content = http.request(error_url, "GET", None, headers)
                except Exception:
                    self.logger.error("Failed to get error message for incident with correlation ID {0}".format(resp.get('correlation_id')))
                    self.logger.error(traceback.format_exc())
                else:
                    if error_response.status == 200:
                        self.logger.error('Error Message: {0}'.format(json.loads(error_content)['result']['error_message']))
                        return {'Error Message': json.loads(error_content)['result']['error_message']}
                    else:
                        self.logger.error("Failed to get error message of Incident creation failure. Status code: {}, response: {}".format(
                            error_response.status, error_content
                        ))
                        return {'Error Message': "Failed to get error message of Incident creation failure. Status code: {}, response: {}".format(
                            error_response.status, error_content
                        )}

        return super(SnowIncidentAlert, self)._handle_response(response, content)

def main():
    handler = SnowIncidentAlert()
    handler.handle()

if __name__ == "__main__":
    main()