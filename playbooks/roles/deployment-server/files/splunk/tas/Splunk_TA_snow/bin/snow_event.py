
# encoding = utf-8
# Always put this line at the beginning of this file
import import_declare_test

import os
import sys

from alert_actions_base import ModularAlertBase
import modalert_snow_event_helper

class AlertActionWorkerSnowEvent(ModularAlertBase):

    def __init__(self, ta_name, alert_name):
        super(AlertActionWorkerSnowEvent, self).__init__(ta_name, alert_name)

    def validate_params(self):

        if not self.get_param("account"):
            self.log_error('account is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("node"):
            self.log_error('node is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("type"):
            self.log_error('type is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("resource"):
            self.log_error('resource is a mandatory parameter, but its value is None.')
            return False

        if not self.get_param("severity"):
            self.log_error('severity is a mandatory parameter, but its value is None.')
            return False
        return True

    def process_event(self, *args, **kwargs):
        status = 0
        try:
            if not self.validate_params():
                return 3
            status = modalert_snow_event_helper.process_event(self, *args, **kwargs)
        except (AttributeError, TypeError) as ae:
            self.log_error("Error: {}. Double check spelling and also verify that a compatible version of "
                           "Splunk_SA_CIM is installed.".format(str(ae)))
            return 4
        except Exception as e:
            msg = "Unexpected error: {}."
            if str(e):
                self.log_error(msg.format(str(e)))
            else:
                import traceback
                self.log_error(msg.format(traceback.format_exc()))
            return 5
        return status

if __name__ == "__main__":
    exitcode = AlertActionWorkerSnowEvent("Splunk_TA_snow", "snow_event").run(sys.argv)
    sys.exit(exitcode)
