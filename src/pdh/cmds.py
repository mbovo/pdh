# from .pd import Incidents
# from .transformations import Transformation
# from .filters import Filter
# from .pd import (
#     STATUS_TRIGGERED,
# )


# def list_incidents(cfg, userid, status, urgencies, alerts, output, filter_re, fields=None, alert_fields=None):
#     pd = Incidents(cfg)
#     incs = pd.list(userid, statuses=status, urgencies=urgencies)
#     if fields is None:
#         fields = ["id", "assignee", "title", "status", "created_at", "last_status_change_at"]
#     else:
#         fields = fields.lower().strip().split(",")
#     if alert_fields is None:
#         alert_fields = ["status", "created_at", "service.summary", "body.details.Condition", "body.details.Segment", "body.details.Scope"]
#     else:
#         alert_fields = alert_fields.lower().strip().split(",")
#     if alerts:
#         for i in incs:
#             i["alerts"] = pd.alerts(i["id"])
#         fields.append("alerts")

#     # Build filtered list for output
#     if output != "raw":
#         transformations = dict()
#         for f in fields:
#             transformations[f] = Transformation.extract_field(f)
#             # special cases
#             if f == "assignee":
#                 transformations[f] = Transformation.extract_assignees()
#             if f == "status":
#                 transformations[f] = Transformation.extract_field("status", ["red", "yellow"], "status", STATUS_TRIGGERED, True)
#             if f == "url":
#                 transformations[f] = Transformation.extract_field("html_url")
#             if f in ["title", "urgency"]:
#                 transformations[f] = Transformation.extract_field(f, check=True)
#             if f in ["created_at", "last_status_change_at"]:
#                 transformations[f] = Transformation.extract_date(f)
#             if f in ["alerts"]:
#                 transformations[f] = Transformation.extract_alerts(f, alert_fields)

#         filtered = Filter.do(incs, transformations, filters=[Filter.regexp("title", filter_re)])
#     else:
#         # raw output, using json format
#         filtered = incs

#     return filtered
