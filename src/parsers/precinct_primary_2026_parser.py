import os

from mn_sos_results import run

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', '2026')

# 2026 State Primary Election, August 11, 2026
# https://electionresults.sos.mn.gov/Select/MediaFiles/Index?ersElectionId=200
if __name__ == '__main__':
    run('20260811', 'primary', OUTPUT_DIR)
