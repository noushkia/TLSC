import argparse
import multiprocessing

from sqlalchemy import create_engine, text

from code_analyzer.time_locked_contracts import parallel_analysis
from utils.db import get_inspect_database_uri

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--para', type=int, help='Number of analyzers', default=2)
    args = parser.parse_args()

    analyzer_cnt = args.para

    # fetch contract bytecodes and addresses from the database
    conn = create_engine(get_inspect_database_uri()).connect()
    # fetch only the active contracts whose addresses are stored in contracts_info table
    query = f"SELECT contracts.contract_address, contracts.bytecode " \
            "FROM contracts " \
            "INNER JOIN contracts_info ON contracts.contract_address = contracts_info.contract_address "
    contracts = conn.execute(text(query))
    contracts = [(row[0], row[1]) for row in contracts]

    parallel_analysis(contracts=contracts, analyzer_cnt=analyzer_cnt)
