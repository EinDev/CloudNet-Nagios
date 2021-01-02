#!/usr/bin/python3
# Version 1.1
import nagiosplugin
import argparse
import urllib.request
import json
import logging

_log = logging.getLogger('nagiosplugin')


class Minecraft(nagiosplugin.Resource):
    def __init__(self, url: str, client_name: str):
        self.url = url
        self.client_name = client_name

    def data(self):
        contents = urllib.request.urlopen(self.url + "/monitor").read()
        services = json.loads(contents)["servers"]
        details = ""
        if not self.client_name in services:
            raise nagiosplugin.CheckError("Cannot find server name: '%s'" % self.client_name)
        if not 'tps' in services[self.client_name]:
            raise nagiosplugin.CheckError("No tps data")
        return services[self.client_name]['tps']

    def probe(self):
        data = self.data()
        _log.debug("got data: %s" % data)
        for i, period in enumerate([1,5,15]):
            yield nagiosplugin.Metric('tps%d' % period, float(round(data[i], 2)), context='tps')

class MinecraftSummary(nagiosplugin.Summary):
    def ok(self, results: nagiosplugin.Results):
        return ', '.join(
            str(float(str(results[r].metric))) for r in ['tps1', 'tps5', 'tps15']
        )

def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='19',
                      help='return warning if tps is below RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='15',
                      help='return critical if tps is below RANGE')
    argp.add_argument('-n', '--name', metavar='NAME', default='',
                      help='name of the service')
    argp.add_argument('-v', '--verbose', action='count', default=0)
    argp.add_argument('address', metavar='http[s]://<hostname>:<port>',
                      help='full address of the webserver, without trailing slash')
    args = argp.parse_args()
    check = nagiosplugin.Check(
        Minecraft(args.address, args.name),
        nagiosplugin.ScalarContext('tps', '%s:' % float(args.warning), '%s:' % float(args.critical)),
        MinecraftSummary()
    )
    check.main(args.verbose)

if __name__ == '__main__':
    main()
