import uuid
import time
import os

import snow_ticket as st


class SnowIncidentBase(st.SnowTicket):

    def _prepare_data(self, event):
        event_data = {}
        url = os.environ.get("SPLUNK_ARG_6", "")

        # (field_name, default_value)
        fields = (("category", None), ("short_description", None), ("description", ""),
                  ("contact_type", None), ("splunk_url", url), ("urgency", ""),("caller_id", ""),
                  ("subcategory", ""), ("business_service", ""), ("state", "4"), ("comments", ""),
                  ("location", ""), ("impact", "3"),("opened_by", "Splunk"), ("u_opened_by_group", "SIEM-Content-Support"),
                  ("correlation_id", ""),
                  ("priority", "4"), ("assignment_group", ""))

        for field, default_val in fields:
            val = event.get(field, default_val)
            if val is None:
                msg = ('Field "{}" is required by ServiceNow to '
                       'create incident').format(field)
                self.logger.error(msg)
                self._handle_error(msg)
                return None

            event_data[field] = val

        if "ciIdentifier" in event:
            ci_ident = event["ciIdentifier"]
        elif "ciidentifier" in event:
            ci_ident = event["ciidentifier"]
        else:
            ci_ident = event.get("ci_identifier", "")

        event_data["configuration_item"] = ci_ident
        if not event_data["correlation_id"].strip():
            event_data["correlation_id"] = self._get_correlation_id(event)

        self.logger.debug("event_data=%s", event_data)
        return event_data

    def _get_correlation_id(self, event):
        return uuid.uuid1(clock_seq=int(time.time())).hex

    def _get_table(self):
        return "x_splu2_splunk_ser_u_splunk_incident"

    def _get_ticket_link(self, sys_id):
        link = "{}incident.do?sysparm_query=correlation_id={}".format(
            self.snow_account["url"], sys_id)

        return link

    def _get_result(self, resp):

        res = {
            "Incident Number": resp["number"],
            "Created": resp["sys_created_on"],
            "Priority": resp["priority"],
            "Updated": resp["sys_updated_on"],
            "Short description": resp["short_description"],
            "Description": resp["description"],
            "Category": resp["category"],
            "Contact Type": resp["contact_type"],
            "ciIdentifier": resp["configuration_item"],
            "State": resp["state"],
            "Sys Id": resp["sys_id"],
            "Incident Link": self._get_ticket_link(resp["correlation_id"]),
            "Correlation ID": resp["correlation_id"],
           #"Contact": resp["caller_id"],
            "Location": resp["location"],
           # "Impacted Service": resp["business_service"],
           # "Opened by Group": resp["u_opened_by_group"],
           # "Opened By": resp["opened_by"], 
            "Splunk URL": resp["splunk_url"],
        }
        return res
