"""Shared parser for Minnesota Secretary of State election results flat files.

Used by the per-election parser scripts (e.g. precinct_general_2026_parser.py,
precinct_primary_2026_parser.py).

File layout (see https://electionresults.sos.mn.gov/Select/MediaFiles/Index):
    State;County ID;Precinct ID;Office ID;Office Name;District;
    Candidate Order Code;Candidate Name;Suffix;Incumbent Code;
    Party Abbreviation;Number of Precincts Reporting;
    Total Number of Precincts;Votes;Percentage;Total Votes for Office

Supporting files:
    Cntytbl.txt  county ID -> county name
    PrctTbl.txt  county ID;precinct ID -> precinct name
"""

import csv
import os

import requests

FILES_BASE = 'https://electionresultsfiles.sos.mn.gov'

# Normalize office names to match prior-year OpenElections conventions.
# The district column already carries the district number/letter.
OFFICE_PREFIX_MAP = [
    ('U.S. Senator', 'U.S. Senate'),
    ('U.S. Representative', 'U.S. House'),
    ('State Senator', 'State Senate'),
    ('State Representative', 'State House'),
]


def standardize_office(name):
    for prefix, standardized in OFFICE_PREFIX_MAP:
        if name.startswith(prefix):
            return standardized
    return name


def download(url):
    """Return the server's response as text, normalizing CR/CRLF to LF."""
    r = requests.get(url)
    r.raise_for_status()
    return r.content.decode('ascii', errors='replace')


def lines(text):
    lines = text.replace('\r\n', '\n').replace('\r', '\n')
    return [line.strip() for line in lines.split('\n') if line.strip()]


def counties(url):
    """county ID -> county name"""
    result = {}
    for line in lines(download(url)):
        fields = line.split(';')
        try:
            result[fields[0].strip()] = fields[1]
        except (IndexError, KeyError):
            continue
    return result


def precincts(url):
    """(county ID, precinct ID) -> precinct name"""
    result = {}
    for line in lines(download(url)):
        fields = line.split(';')
        try:
            result[(fields[0].strip(), fields[1].strip())] = fields[2]
        except (IndexError, KeyError):
            continue
    return result


def parse_file(text, county_lookup, precinct_lookup):
    results = []
    for line in lines(text):
        fields = line.split(';')
        # State;county;precinct;office_code;office;district;cand_code;
        # candidate;suffix;incumbent;party;pcts_reporting;pcts_total;
        # votes;pct;total_votes
        county_code = fields[1].strip()
        precinct_code = fields[2].strip()
        county = county_lookup.get(county_code, '')
        if precinct_code:
            key = (county_code, precinct_code)
            precinct = precinct_lookup.get(key, '')
            if not precinct:
                raise ValueError('No precinct name for {0}'.format(key))
        else:
            precinct = ''
        results.append({
            'county': county,
            'precinct': precinct,
            'office': standardize_office(fields[4].strip()),
            'district': fields[5].strip(),
            'party': fields[10].strip(),
            'candidate': fields[7].strip(),
            'votes': fields[13].strip(),
        })
    return results


def precinct_stats(text, county_lookup, precinct_lookup):
    """One row per precinct of voting statistics.

    pctstats.txt layout (see the MediaFiles documentation):
        State;County ID;Precinct ID;Precinct Name;
        Has Reported Statistics (1/0);
        Registered as of 7:00 a.m. Election Day;
        Registered on Election Day;
        Signatures on the Polling Place Roster;
        Regular, Military, and Overseas Absentee Ballots;
        Federal-Only Absentee Ballots;
        President-Only Absentee Ballots;
        Total Number Voted
    """
    stats = []
    for line in lines(text):
        fields = line.split(';')
        county_code = fields[1].strip()
        precinct_code = fields[2].strip()
        key = (county_code, precinct_code)
        expected = precinct_lookup.get(key)
        name = fields[3].strip()
        if expected is not None and expected.upper() != name.upper():
            raise ValueError(
                'Precinct name mismatch for {0}: file says {1!r}, '
                'PrctTbl says {2!r}'.format(key, name, expected))
        stats.append({
            'county': county_lookup.get(county_code, ''),
            'precinct_code': precinct_code,
            'precinct': name,
            'stats_reported': fields[4].strip(),
            'registered_at_7am': int(fields[5]),
            'registered_election_day': int(fields[6]),
            'roster_signatures': int(fields[7]),
            'absentee_ballots': int(fields[8]),
            'federal_only_absentee_ballots': int(fields[9]),
            'president_only_absentee_ballots': int(fields[10]),
            'total_voted': int(fields[11]),
        })
    return stats


def write_csv(results, filename, header):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for row in results:
            writer.writerow([row[col] for col in header])


def run(election_date, election_name, output_dir='..'):
    """Parse one election and write precinct- and county-level CSVs.

    election_date: the date folder on the files server, e.g. '20261103'
    election_name: e.g. 'general' or 'primary'
    output_dir: where the election year's data directory lives
    """
    base = FILES_BASE + '/' + election_date
    county_lookup = counties(base + '/Cntytbl.txt')
    precinct_lookup = precincts(base + '/PrctTbl.txt')

    precinct_results = parse_file(
        download(base + '/allracesbyprecinct.txt'), county_lookup,
        precinct_lookup)
    county_results = parse_file(
        download(base + '/allracesbycounty.txt'), county_lookup,
        precinct_lookup)

    stem = '{0}__mn__{1}'.format(election_date, election_name)
    precinct_file = os.path.join(
        output_dir, stem + '__precinct.csv')
    header = ['county', 'precinct', 'office', 'district', 'party',
              'candidate', 'votes']
    write_csv(precinct_results, precinct_file, header)
    print('Wrote {0} rows to {1}'.format(len(precinct_results), precinct_file))

    county_file = os.path.join(
        output_dir, stem + '__county.csv')
    county_header = ['county', 'office', 'district', 'party', 'candidate',
                     'votes']
    write_csv(county_results, county_file, county_header)
    print('Wrote {0} rows to {1}'.format(len(county_results), county_file))

    stats = precinct_stats(
        download(base + '/pctstats.txt'), county_lookup, precinct_lookup)
    stats_header = ['county', 'precinct_code', 'precinct', 'stats_reported',
                    'registered_at_7am', 'registered_election_day',
                    'roster_signatures', 'absentee_ballots',
                    'federal_only_absentee_ballots',
                    'president_only_absentee_ballots', 'total_voted']
    stats_file = os.path.join(
        output_dir, stem + '__precinct_stats.csv')
    write_csv(stats, stats_file, stats_header)
    print('Wrote {0} rows to {1}'.format(len(stats), stats_file))
