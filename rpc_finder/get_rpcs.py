import json

import requests

import pandas as pd

# get 100 ips with each request
batch_length = 100

client = "erigon"

ETHERNODES_URL = ("https://ethernodes.org/data?draw=9&columns%d5B0%5D%5Bdata%5D=id&columns%5B0%5D%5Bname%5D=&columns"
                  "%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=true&columns%5B0%5D%5Bsearch%5D%5Bvalue"
                  "%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=host&columns%5B1%5D"
                  "%5Bname%5D=&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D"
                  "%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=isp"
                  "&columns%5B2%5D%5Bname%5D=&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true"
                  "&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D"
                  "%5Bdata%5D=country&columns%5B3%5D%5Bname%5D=&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D"
                  "%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D"
                  "=false&columns%5B4%5D%5Bdata%5D=client&columns%5B4%5D%5Bname%5D=&columns%5B4%5D%5Bsearchable%5D"
                  "=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D"
                  "%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=clientVersion&columns%5B5%5D%5Bname%5D"
                  "=&columns%5B5%5D%5Bsearchable%5D=true&columns%5B5%5D%5Borderable%5D=true&columns%5B5%5D%5Bsearch"
                  "%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=os&columns"
                  "%5B6%5D%5Bname%5D=&columns%5B6%5D%5Bsearchable%5D=true&columns%5B6%5D%5Borderable%5D=true&columns"
                  "%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata"
                  "%5D=lastUpdate&columns%5B7%5D%5Bname%5D=&columns%5B7%5D%5Bsearchable%5D=true&columns%5B7%5D"
                  "%5Borderable%5D=true&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D"
                  "=false&columns%5B8%5D%5Bdata%5D=inSync&columns%5B8%5D%5Bname%5D=&columns%5B8%5D%5Bsearchable%5D"
                  "=true&columns%5B8%5D%5Borderable%5D=true&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D"
                  "%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=8&order%5B0%5D%5Bdir%5D=desc&start={"
                  "start}&length={length}&search%5Bvalue%5D={client}&search%5Bregex%5D=false&_=1661254019057")


def get_number_of_records():
    r = requests.get(ETHERNODES_URL.format(start=0, length=batch_length, client=client))
    return json.loads(r.text)['recordsTotal']


if __name__ == "__main__":
    total_records = get_number_of_records()

    hosts_list = []

    for i in range(0, total_records, batch_length):
        print(f"Fetching hosts {i} to {min(i + batch_length, total_records)}")
        response = requests.get(ETHERNODES_URL.format(start=i, length=batch_length, client=client))
        rows = json.loads(response.text)['data']
        hosts_list.extend(rows)

    hosts_df = pd.DataFrame(hosts_list, columns=["id", "host", "port", "client", "clientVersion", "os",
                                                 "lastUpdate", "country", "inSync", "isp"])
    hosts_df.drop(hosts_df[hosts_df['inSync'] == 0].index, inplace=True)

    with open(f"{client}_hosts.csv", "w", encoding="utf-8") as f:
        for host in hosts_df['host']:
            f.write(host + '\n')
