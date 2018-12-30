import requests
import csv

def generate_candidates(url):
    candidates = []
    r = requests.get(url)
    lines = r.text.split('\r\n')
    for line in lines:
        cand = line.split(';')
        try:
            candidates.append({"id": cand[0], "name": cand[1], "office_code": cand[2], "office": cand[3], "party_code": cand[5], "party": cand[6]})
        except:
            pass
    return candidates

def counties():
    counties = []
    r = requests.get("https://electionresults.sos.state.mn.us/Results/MediaSupportResult/2?mediafileid=6")
    lines = r.text.split('\r\n')
    for line in lines:
        try:
            county_code, county, fill = line.strip().split(';')
            counties.append({'county_code': county_code.strip(), 'county': county})
        except:
            continue
    return counties

def parse_file(url, counties):
    results = []
    r = requests.get(url)
    lines = r.text.split('\r\n')
    for line in lines:
        result = line.split(';')
        try:
            county = [x['county'] for x in counties if result[1] == x['county_code']][0]
            if "U.S. Representative District" in result[4]:
                office = 'U.S. House'
                district = result[5]
            elif 'State Representative District' in result[4]:
                office = 'State House'
                district = result[5]
            elif 'State Senator District' in result[4]:
                office = 'State Senate'
                district = result[5]
            elif "U.S. Senator Special Election" in result[4]:
                office = 'U.S. Senate'
                district = 'Unexpired Term'
            elif "U.S. Senator" in result[4]:
                office = 'U.S. Senate'
                district = result[5]
            else:
                office = result[4]
                district = result[5]
            results.append({"county_code": result[1], "county": county, "office_code": result[3], "office": office, "district": district, "candidate_code": result[6], "candidate": result[7], "party": result[10], "votes": result[13], "pct": result[14]})
        except:
            pass
    return results

def write_csv(results):
    filename = '20120814__mn__primary__county.csv'
    with open(filename, 'w') as csvfile:
         w = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
         w.writerow(['county_code', 'county', 'office', 'district', 'party', 'candidate', 'votes', 'pct'])
         for row in results:
            w.writerow([row['county_code'], row['county'], row['office'], row['district'], row['party'], row['candidate'], row['votes'], row['pct']])


if __name__ == "__main__":
    url = 'https://electionresults.sos.state.mn.us/Results/MediaResult/2?mediafileid=38'
    candidates = generate_candidates('https://electionresults.sos.state.mn.us/Results/MediaSupportResult/2?mediafileid=82')
    counties = counties()
    results = parse_file(url, counties)
    write_csv(results)
