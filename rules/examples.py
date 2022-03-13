#!/usr/bin/env python3

# Needed imports
from pdh import rules, Filter


# This annotation make the main() method parse stdin as json into the parameter called input
# All returned values are converted to json and printed to stdout
@rules.rule
def main(input):

    # Initialize PagerDuty's APIs
    api = rules.api()

    # From the given input extract only incidents with the word cassandra in title
    incs = Filter.objects(input, filters=[Filter.regexp("title", ".*EC2.*")])

    # ackwnoledge all previously filtered incidents
    api.ack(incs)

    # # resolve all previously filtered incidents
    # api.resolve(incs)

    # # snooze all previously filtered incidents for 1h
    # api.snooze(incs, duration=3600)

    # # Chain a given rule, i.e call that rule with the output of this one
    # # chain-loading supports only a single binary, not directories
    # c = rules.chain(incs, "rules/test_chaining.sh")

    # # Execute an external program and get the output/err/return code
    # p: rules.ShellResponse = rules.exec('kubectl get nodes -o name')
    # if p.rc > 0:
    #     nodes = p.stdout.split("\n")

    # if you return a dict will be rendered with each item as a column in a table
    # Othrwise will be converted as string
    return {i["id"]: i["summary"] for i in incs}


if __name__ == "__main__":
    main()
