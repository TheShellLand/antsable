import snow_ticket as st


class ManualSnowChange(st.SnowTicket):
    """
    Create ServiceNow Change manually by running the script and passing
    in the correct parameters
    """

    def __init__(self):
        super(ManualSnowChange, self).__init__()

    def _get_events(self):
        (arg_parser, create_parser, update_parser) = self._create_arg_parsers()

        # create subcommand
        create_parser.add_argument("--category", dest="category", type=str,
                                   action="store", default="Other",
                                   help="Category of the change")
        create_parser.add_argument("--short_description",
                                   dest="short_description",
                                   type=str, action="store", required=True,
                                   help="Short description of the change")
        create_parser.add_argument("--type", dest="type", type=str,
                                   action="store", default="Comprehensive",
                                   help="Type of the change")
        create_parser.add_argument("--approval", dest="approval", type=str,
                                   action="store", default="not requested",
                                   help="Approval of the change")
        create_parser.add_argument("--state", dest="state", type=int,
                                   action="store", default=1,
                                   help="State of the event")
        create_parser.add_argument("--impact", dest="impact", type=int,
                                   action="store", default=3,
                                   help="Impact of the change")
        create_parser.add_argument("--risk", dest="risk", type=int,
                                   action="store", default=3,
                                   help="Risk of the change")
        create_parser.add_argument("--priority", dest="priority", type=int,
                                   action="store", default=4,
                                   help="Priority of the change")
        create_parser.add_argument("--assigned_to", dest="assigned_to",
                                   type=str, action="store", default="",
                                   help="Person primarily responsible for"
                                   "working this task")
        create_parser.add_argument("--start_date", dest="start_date",
                                   type=str, action="store", default="",
                                   help='Planned start date of this change in '
                                   '"YYYY-MM-DD hh:mm:ss" format')
        create_parser.add_argument("--end_date", dest="end_date",
                                   type=str, action="store", default="",
                                   help='Planned end date of this change in '
                                   '"YYYY-MM-DD hh:mm:ss" format')
        create_parser.add_argument("--requested_by", dest="requested_by",
                                   type=str, action="store",
                                   default=self.snow_account["username"],
                                   help="Requested by")
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
            # FIXME verify start_date/end_date
            return ({
                "category": opts.category,
                "short_description": opts.short_description,
                "type": opts.type,
                "approval": opts.approval,
                "state": opts.state,
                "impact": opts.impact,
                "risk": opts.risk,
                "priority": opts.priority,
                "start_date": opts.start_date,
                "end_date": opts.end_date,
                "assigned_to": opts.assigned_to,
                "requested_by": opts.requested_by,
                "description": opts.additional_info,
            },)

    def _get_table(self):
        return "change_request"

    def _get_result(self, resp):
        return {
            "Change Number": resp["number"],
            "Short description": resp["short_description"],
            "Approval": resp["approval"],
            "Type": resp["type"],
            "State": resp["state"],
            "Planned start date": resp["start_date"],
            "Planned end date": resp["end_date"],
            "Assigned to": resp["assigned_to"],
            "Sys Id": resp["sys_id"],
            "Change Link": self._get_ticket_link(resp["sys_id"]),
        }


def main():
    handler = ManualSnowChange()
    handler.handle()


if __name__ == "__main__":
    main()
