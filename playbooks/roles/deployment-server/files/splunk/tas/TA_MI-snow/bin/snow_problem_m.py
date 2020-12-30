import time


import snow_ticket as st


class ManualSnowProblem(st.SnowTicket):
    """
    Create ServiceNow problem manually by running the script and passing
    in the correct parameters
    """

    def __init__(self):
        super(ManualSnowProblem, self).__init__()

    def _get_events(self):
        (arg_parser, create_parser, update_parser) = self._create_arg_parsers()

        # create subcommand
        create_parser.add_argument("--short_description",
                                   dest="short_description",
                                   type=str, action="store", required=True,
                                   help="Short description of the problem")
        create_parser.add_argument("--known_error", dest="known_error",
                                   type=bool, action="store", default=False,
                                   help="Root cause is understood, and a "
                                   "temporary workaround or permanent fix "
                                   "exists")
        create_parser.add_argument("--knowledge", dest="knowledge", type=bool,
                                   action="store", default=False,
                                   help="If specified, will automatically "
                                   "create a draft knowledge article upon "
                                   "closure")
        create_parser.add_argument("--opened_at", dest="opened_at", type=str,
                                   action="store", default="",
                                   help='Opened at. In format of "YYYY-MM-DD '
                                   'hh:mm:ss"')
        create_parser.add_argument("--state", dest="state",
                                   type=int, action="store", default=1,
                                   help="State of the problem")
        create_parser.add_argument("--priority", dest="priority", type=int,
                                   action="store", default=4,
                                   help="Priority of the problem")
        create_parser.add_argument("--assignment_group",
                                   dest="assignment_group",
                                   type=str, action="store", default="",
                                   help="Assignment groups")
        create_parser.add_argument("--assigned_to", dest="assigned_to",
                                   type=str, action="store", default="",
                                   help="Person primarily responsible for "
                                   "working this task")
        create_parser.add_argument("--opened_by", dest="opened_by",
                                   type=str, action="store",
                                   default=self.snow_account["username"],
                                   help="Opened by")
        create_parser.add_argument("--additional_info", dest="additional_info",
                                   type=str, action="store", default="",
                                   help="Additional information")
        opts = arg_parser.parse_args()
        # self.subcommand = opts.subcommand

        if self.subcommand == "update":
            self.sys_id = opts.sys_id
            return ({
                "state": opts.state,
            },)
        else:
            # FIX ME timestamp verification
            opened_at = opts.opened_at
            if not opened_at:
                opened_at = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

            return ({
                "short_description": opts.short_description,
                "known_error": opts.known_error,
                "knowledge": opts.knowledge,
                "opened_at": opened_at,
                "state": opts.state,
                "priority": opts.priority,
                "assignment_group": opts.assignment_group,
                "assigned_to": opts.assigned_to,
                "opened_by": opts.opened_by,
                "description": opts.additional_info,
            },)

    def _get_table(self):
        return "problem"

    def _get_result(self, resp):
        return {
            "Problem Number": resp["number"],
            "Short description": resp["short_description"],
            "Related Incidents": resp["related_incidents"],
            "State": resp["state"],
            "Sys Id": resp["sys_id"],
            "Problem Link": self._get_ticket_link(resp["sys_id"]),
        }


def main():
    handler = ManualSnowProblem()
    handler.handle()


if __name__ == "__main__":
    main()
