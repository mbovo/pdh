#!/usr/bin/env python3

# Needed imports
from pdh import rules, Filter


# This annotation make the main() method automatically parse json input into input variable
# And all returned values are converted to json
@rules.rule
def main(input):

    incs = Filter.objects(input, filters=[Filter.regexp("title", ".*cassandra.*")])

    # if you return a dict will be rendered with each item as a column in a table
    # Othrwise will be converted as string
    return {i["id"]: i["summary"] for i in incs}


if __name__ == "__main__":
    main()
