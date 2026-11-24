import os

from mn_sos_results import run

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '2026')

# 2026 State General Election, November 3, 2026
# https://electionresults.sos.mn.gov/Select/MediaFiles/Index?ersElectionId=201
if __name__ == '__main__':
    run('20261103', 'general', OUTPUT_DIR)
