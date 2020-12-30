import snow_incident_base as sib
import snow_ticket as st


class ManualSnowIncident(sib.SnowIncidentBase):
    """
    Create ServiceNow incident manually by running the script and passing
    in the correct parameters
    """

    def __init__(self):
        super(ManualSnowIncident, self).__init__()

    def _get_events(self):
        create_parser = st.ArgumentParser()

        # create subcommand
        create_parser.add_argument("--category", dest="category", type=str,
                                   action="store", required=True,
                                   help="Category of the incident")
        create_parser.add_argument("--description",
                                   dest="description",
                                   type=str, action="store", required=False,
                                   help="Long description of the incident")
        create_parser.add_argument("--short_description",
                                   dest="short_description",
                                   type=str, action="store", required=True,
                                   help="Short description of the incident")
        create_parser.add_argument("--contact_type", dest="contact_type",
                                   type=str, action="store", required=True,
                                   help="Contact type of the incident")
        create_parser.add_argument("--caller_id", dest="caller_id",
                                   type=str, action="store", required=False,
                                   help="Contact")
        create_parser.add_argument("--urgency", dest="urgency", type=int,
                                   action="store", default=3,
                                   help="Urgency of the incident")
        create_parser.add_argument("--subcategory", dest="subcategory",
                                   type=str, action="store", default="",
                                   help="Subcategory of the incident")
        create_parser.add_argument("--state", dest="state",
                                   type=int, action="store", default=4,
                                   help="State of the incident")
        create_parser.add_argument("--location", dest="location",
                                   type=str, action="store", default="",
                                   help="Location of the incident")
        create_parser.add_argument("--impact", dest="impact",
                                   type=int, action="store", default=3,
                                   help="Impact of the incident")
	create_parser.add_argument("--business_service", dest="business_service",
                                   type=str, action="store", default="",
                                   help="Impacted Service")
        create_parser.add_argument("--priority", dest="priority", type=int,
                                   action="store", default=4,
                                   help="Priority of the incident")
        create_parser.add_argument("--assignment_group",
                                   dest="assignment_group",
                                   type=str, action="store", default="",
                                   help="Assignment groups")
        create_parser.add_argument("--opened_by", dest="opened_by",
                                   type=str, action="store",
                                   default=self.snow_account["username"],
                                   help="Opened by")
	create_parser.add_argument("--u_opened_by_group", dest="u_opened_by_group",
                                   type=str, action="store",
                                   default=self.snow_account["username"],
                                   help="Opened by Group")
        create_parser.add_argument("--ci_identifier", dest="ci_identifier",
                                   type=str, action="store", default="",
                                   help="Optional JSON string that represents "
                                   "a configuration item in the users network")

        create_parser.add_argument("--comments", dest="comments",
                                   type=str, action="store", default="",
                                   help="Incident comments")
        create_parser.add_argument("--splunk_url", dest="splunk_url",
                                   type=str, action="store", default="",
                                   help="Splunk deepdive URL")
        create_parser.add_argument("--correlation_id",
                                   dest="correlation_id", type=str,
                                   action="store", default="",
                                   help="Splunk deepdive URL")

        opts = create_parser.parse_args()
        # self.subcommand = opts.subcommand

        if self.subcommand == "update":
            self.sys_id = opts.sys_id
            return ({
                "u_state": opts.state,
            },)
        else:
            rec = {
                "category": opts.category,
                "short_description": opts.short_description,
		"description": opts.description,
                "contact_type": opts.contact_type,
                "caller_id": opts.caller_id,
                "urgency": str(opts.urgency),
                "subcategory": opts.subcategory,
                "state": str(opts.state),
                "location": opts.location,
		"business_service": opts.business_service,
		"u_opened_by_group": opts.u_opened_by_group,
                "impact": str(opts.impact),
                "priority": str(opts.priority),
                "assignment_group": opts.assignment_group,
                "opened_by": opts.opened_by,
                "ciidentifier": opts.ci_identifier,
            }

            rec["comments"] = opts.comments
            rec["splunk_url"] = opts.splunk_url
            rec["correlation_id"] = opts.correlation_id
            return (rec,)


def main():
    handler = ManualSnowIncident()
    handler.handle()


if __name__ == "__main__":
    main()
