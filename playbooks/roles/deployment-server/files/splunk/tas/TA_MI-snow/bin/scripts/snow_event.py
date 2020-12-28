import os
import os.path as op
import sys

sys.path.insert(0, op.dirname(op.dirname(op.abspath(__file__))))

import snow_event_base as seb
import snow_ticket as st


class AutomaticSnowEvent(seb.SnowEventBase):
    """
    Create ServiceNow Event automatically by running as a callback script
    when the corresponding alert is fired
    """

    def _get_events(self):
        return st.read_alert_results(os.environ["SPLUNK_ARG_8"], self.logger)


def main():
    handler = AutomaticSnowEvent()
    handler.handle()


if __name__ == "__main__":
    main()
