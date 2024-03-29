#!/usr/bin/env python3
# Get list of bin collection dates from Portsmouth City Council website
# TODO This is a bit on the hacky side, not really robust at all, we should probably check that requests have completed properly rather than just assuming and just generally do everything better
#      FYI The reply from runLookup has a 'status' field that should be set to 'done', maybe use this??? or it might be nothing, also check for HTTP code 200 maybe????
# Notes:
#   - I noticed a CSRF floating around the website, if things go wrong we might need to use this as well
#   - There are AWS cookies too .. I'm not sure how much is hosted in AWS and if AWS will get upset if they aren't about so might need to look at those too
#   - Most GETs and POSTs have an aweful lot more arguments sent and received, cookies too, so might need to include some. '_' seems to be a timestamp and 'sid' is sent to a lot too (session id, extracted when doing auth below)

import sys
from http.client import HTTPSConnection
import json
from datetime import datetime


class PortsmouthCouncilAPI:
    """ Interact with PCCs website API """
    def __init__(self, host='my.portsmouth.gov.uk'):  # Note: Host is configurable because it looks like PCC website is based on a third party system so this stuff might work with other websites ... maybe
        """ Create connection to host
        host - This is configurable on the off chance this can be used with another councils website
        """
        self.conn = HTTPSConnection(host)
        self.phpsessid = None
        self.auth()

    def auth(self):
        """ Authenticate with API """
        self.conn.request('GET', '/authapi/isauthenticated')

        resp = self.conn.getresponse()
        auth_obj = json.loads(resp.read())
        self.sid = auth_obj['auth-session']  # Note: I don't think this is needed

        set_cookie = resp.getheader('Set-Cookie')
        cookies = {}
        # Super hacky cookie extraction - TODO Probably should do this properly
        for c in set_cookie.split(','):
            c = c.split(';')[0]
            if '=' in c:
                c = c.strip()
                c = c.split('=')
                cookies[c[0]] = c[1]

        self.phpsessid = cookies['PHPSESSID']

        headers = {'cookie': f'PHPSESSID={cookies["PHPSESSID"]}'}

    def lookup(self, id, fields):
        """ POST to runLookup
        id - The id to pass to runLookup
        fields - Dictionary of fields to use for lookup
        Returns decoded JSON of response
        """
        # TODO find out if we really want to use 'fields' argument as it's used ... perhaps runLookup is more versatile than this ... can probably deal with this if we ever need to expand this class
        headers = {'cookie' : f'PHPSESSID={self.phpsessid}'}
        field_data = {k:{'value':v} for k,v in fields.items()}
        data = {'formValues': {'Section 1': field_data}}

        self.conn.request('POST', f'/apibroker/runLookup?id={id}', body=json.dumps(data), headers=headers)
        resp = self.conn.getresponse()
        return json.loads(resp.read())

    def lookup_uprn(self, postcode, filter='', exact=False):
        """ Get list of addresses and UPRNs
        postcode - Postcode to lookup
        filter - String used to filter addresses. Only addresses that contain this string are returned. Defaults to an empty string
        exact - Whether the filter should be treated as an exact match, best used for low number addresses (e.g. number 1 could match 11, 21, 31 etc easily too). Defaults to False
        Returns list of addresses and UPRNs
        """
        addr_data = self.lookup('58ca773b44b4b', {'postcode_search_after': postcode})
        addr_data = addr_data['integration']['transformed']['select_data']
        if exact:
            addr = [{'addr': item['label'], 'uprn': item['value']} for item in addr_data if filter == item['label']]
        else:
            addr = [{'addr': item['label'], 'uprn': item['value']} for item in addr_data if filter in item['label']]
        return addr

    def lookup_bins(self, uprn):
        """ Get list of bin collection dates from UPRN)
        uprn - UPRN of property to get collection dates for
        Returns dictionary containing list of collection dates for General Rubbish and Recycling
        """
        dates_data = self.lookup('5e81ed10c0241', {'col_uprn': uprn})
        dates_data = dates_data['integration']['transformed']['rows_data']['0']
        rubbish = dates_data['listRefDatesHTML'].split('<p>')[0].split('<br />')
        recycling = dates_data['listRecDatesHTML'].split('<p>')[0].split('<br />')
        rubbish = [datetime.strptime(date.strip('*'), '%A %d %B %Y').date().isoformat() for date in rubbish if date != '']
        recycling = [datetime.strptime(date.strip('*'), '%A %d %B %Y').date().isoformat() for date in recycling if date != '']
        return {'rubbish': rubbish, 'recycling': recycling}

    def get_bin_dates(self, postcode, filter='', exact=False):
        """ Get list of bin collection dates
        postcode - Postcode to lookup
        filter - String used to filter addresses. Only addresses that contain this string are returned. Defaults to an empty string
        exact - Whether the filter should be treated as an exact match, best used for low number addresses (e.g. number 1 could match 11, 21, 31 etc easily too). Defaults to False
        Returns dictionary containing list of collection dates for General Rubbish and Recycling
        Bin Collection Date Lookup: https://my.portsmouth.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-26e27e70-f771-47b1-a34d-af276075cede/AF-Stage-cd7cc291-2e59-42cc-8c3f-1f93e132a2c9/definition.json
        """
        uprn = self.lookup_uprn(postcode, filter, exact)
        if len(uprn) > 1:
            raise Exception(f'Multiple addresses found at postcode "{postcode}" for filter "{filter}":\n ' + '\n '.join([repr(addr['addr']) for addr in uprn]))
        if len(uprn) == 0:
            raise Exception(f'Address not found')
        uprn = uprn[0]['uprn']
        return self.lookup_bins(uprn)


if __name__ == '__main__':
    postcode = sys.argv[1]
    if len(sys.argv) >= 3:
        filter = sys.argv[2]
    else:
        filter = ''
    if len(sys.argv) >= 4 and sys.argv[3] == 'exact':
        exact = True
    else:
        exact = False

    try:
        api = PortsmouthCouncilAPI()
        dates = api.get_bin_dates(postcode, filter, exact)
        print(json.dumps(dates))
    except Exception as err:
        print(err)
