import time


import snow_event_base as seb
import snow_ticket as st


class ManualSnowEvent(seb.SnowEventBase):
    """
    Create ServiceNow Event manually by running the script and passing
    in the correct parameters
    """

    def __init__(self):
        super(ManualSnowEvent, self).__init__()

    def _get_events(self):
        create_parser = st.ArgumentParser()

        # create subcommand
        create_parser.add_argument("--node", dest="node", type=str,
                                   action="store", required=True,
                                   help="The physical device or virtual entity"
                                   " that is being monitored")
        create_parser.add_argument("--resource", dest="resource", type=str,
                                   action="store", required=True,
                                   help="The resource on the node that "
                                   "generates the event")
        create_parser.add_argument("--type", dest="type", type=str,
                                   action="store", required=True,
                                   help="Type of the event")
        create_parser.add_argument("--severity", dest="severity", type=str,
                                   action="store", required=True,
                                   help="Severity of the event")
        create_parser.add_argument("--source", dest="source", type=str,
                                   action="store", default="",
                                   help="Source of the event")
        create_parser.add_argument("--time_of_event", dest="time_of_event",
                                   type=str, action="store", default="",
                                   help='Time of the event in "YYYY-MM-DD '
                                   'hh:mm:ss" format')
        create_parser.add_argument("--ci_identifier", dest="ci_identifier",
                                   type=str, action="store", default="{}",
                                   help="Optional JSON string that represents "
                                   "a configuration item in the users network")
        create_parser.add_argument("--additional_info", dest="additional_info",
                                   type=str, action="store", default="",
                                   help="Additional information of the event")
        create_parser.add_argument("--description", dest="description",
                                   type=str, action="store", default="",
                                   help="Description of the event")
        opts = create_parser.parse_args()
        # self.subcommand = opts.subcommand

        if self.subcommand == "update":
            self.sys_id = opts.sys_id
            return ({
                "state": opts.state,
            })
        else:
            if not opts.time_of_event:
                time_of_event = time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.gmtime())
            else:
                time_of_event = opts.time_of_event

            res = {
                "node": opts.node,
                "resource": opts.resource,
                "type": opts.type,
                "severity": opts.severity,
                "source": opts.source,
                "time_of_event": time_of_event,
                "ci_identifier": opts.ci_identifier,
                "additional_info": opts.additional_info,
                "description": opts.description
            }

            res["event_class"] = "Splunk"
            return (res,)


def main():
    handler = ManualSnowEvent()
    handler.handle()


if __name__ == "__main__":
    main()
