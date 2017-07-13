import requests
import unicodecsv

def generate_candidates(url):
    candidates = []
    r = requests.get(url)
    lines = r.text.strip().split('\r') # removes all leading and trailing whitespace before splitting
    for line in lines:
        cand = line.strip().split(';') # removes all leading and trailing whitespace before splitting
        candidates.append({"id": cand[0], "name": cand[1], "office_code": cand[2], "office": cand[3], "party_code": cand[5], "party": cand[6]})
    return candidates

def counties():
    counties = []
    r = requests.get("http://minnesotaelectionresults.sos.state.mn.us/Results/MediaSupportResult/100?mediafileid=6") # precinct URL updated
    lines = r.text.split('\r\n')
    for line in lines:
        try:
            county_code, county, fill = line.strip().split(';')
            counties.append({'county_code': county_code.strip(), 'county': county})
        except:
            continue
    return counties

def precincts():
    precincts = []
    r = requests.get("http://minnesotaelectionresults.sos.state.mn.us/Results/MediaSupportResult/100?mediafileid=4") # precinct URL updated 
    lines = r.text.strip().split('\r\n') # removes all leading and trailing whitespace before splitting
    for line in lines:
        try:
            county_code, precinct_code, precinct_name, cong_dist, mn_house_dist, county_comm_dist, jud_dist, swc_dist, fips_code, fill = line.strip().split(';') # fips_code (MCD FIPS Code) added since it is now present in the precinct files
            precincts.append({'county_code': county_code.strip(), 'precinct_code': precinct_code, 'precinct_name': precinct_name, 'cong_dist': cong_dist, 'mn_house_dist': mn_house_dist, 'county_comm_dist': county_comm_dist, 'jud_dist':jud_dist, 'swc_dist': swc_dist })
        except:
            continue
    return precincts

def parse_file(url, counties, precincts):
    results = []
    r = requests.get(url)
    lines = r.text.strip().split('\r') # removes all leading and trailing whitespace before splitting
    for line in lines:
        result = line.split(';')
        try:
            county = [x['county'] for x in counties if result[1] == x['county_code']][0]
            precinct = [x['precinct_name'] for x in precincts if result[2] == x['precinct_code']][0]
            results.append({"county_code": result[1], "county": county, "precinct_code": result[2], "precinct": precinct, "office_code": result[3], "office": result[4], "district": result[5], "candidate_code": result[6], "candidate": result[7], "party": result[10], "votes": result[13], "pct": result[14]})
        except:
            raise
    return results

def write_csv(results):
    filename = '20161108__mn__general__precinct.csv' # updated file name for 2016 General
    with open(filename, 'wb') as csvfile:
         w = unicodecsv.writer(csvfile, encoding='utf-8')
         w.writerow(['county_code', 'county', 'precinct_code', 'precinct', 'office', 'district', 'party', 'candidate', 'votes', 'pct'])
         for row in results:
            w.writerow([row['county_code'], row['county'], row['precinct_code'], row['precinct'], row['office'], row['district'], row['party'], row['candidate'], row['votes'], row['pct']])


results_url = 'http://electionresults.sos.state.mn.us/Results/MediaResult/100?mediafileid=13'

cand_url = 'http://electionresults.sos.state.mn.us/Results/MediaSupportResult/100?mediafileid=82'

gc = generate_candidates(cand_url)

c = counties()

p = precincts()

res = parse_file(results_url, c, p)

write_csv(res)
