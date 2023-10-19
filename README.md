# TLSC

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A tool that finds smart contracts with time locks on Ethereum main-net

## Table of Contents

- [Install](#install)
- [Usage](#usage)
    - [RPC Finder](#rpc-finder)
    - [Time Lock Inspector](#time-lock-smart-contract-inspector)
    - [Contract Inspector](#contract-inspector)
    - [Block Inspector](#block-inspector)
    - [Database](#database)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [References](#references)
- [TODO](#todo)

## Install

### Dependencies

#### PostgreSQL

To install PostgreSQL run the following command:

```bash
sudo apt-get install postgresql postgresql-contrib
```

#### pg_config

To install pg_config and Build psycopg2 from Source, run the following command:

```bash
sudo apt-get install libpq-dev
```

### Requirements

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip3 install -r requirements.txt
```

### Configuration

#### PostgreSQL

To configure PostgreSQL run the following command:

```bash
sudo -u postgres psql
```

If it's your first time running the tool on a system, run the following commands in the PostgreSQL shell:

```bash
CREATE DATABASE tlsc;

CREATE USER kia WITH PASSWORD 'tlsc';

GRANT ALL PRIVILEGES ON DATABASE tlsc TO kia;
```

## Usage

### RPC Finder

The rpc_finder package is used to find RPC endpoints for Erigon Ethereum nodes.
It first fetches the list of synced Erigon nodes from Ethernodes.org and then checks if they are responding to JSON-RPC
requests.
The list of all running RPC endpoints is then stored in erigon_sorted_hosts.csv file.

In order to fetch all possible RPC endpoints, run the following command:

```bash
  python rpc_finder/get_rpcs.py
```

After fetching all possible endpoints, in order to fetch only the RPC endpoints that are responding to JSON-RPC
requests and are up-to-date, run the following command:

```bash
  python rpc_finder/rpc_vitals_check.py
```

### Time Lock Smart Contract Inspector

The tlsc_inspector package is used to inspect a given range of Ethereum blocks for contracts that have time locks.
It first fetches the list of all running RPC endpoints from erigon_sorted_hosts.csv file.
Then it starts up a number of processes to inspect blocks in parallel.
Each process then runs several threads to fetch blocks from the RPC endpoints and inspect them for the contracts.
The results are then stored in the PostgreSQL database.
Each entry of the database has the following fields:

1. contract_address: The address of the contract
2. bytecode: The bytecode of the contract
3. from_address: The address that created the contract
4. tx_hash: The hash of the transaction that created the contract
5. block_number: The block number in which the contract was created

In order to inspect a given range of blocks, run the following command:

```bash
  python inspect_many.py -a START_BLOCK_RANGE -b END_BLOCK_RANGE
```

The inspector by default starts up as many processes as the number of available cpu cores.
You can specify the number of processes to start up by using the -p flag:

```bash
  python inspect_many.py -a START_BLOCK_RANGE -b END_BLOCK_RANGE -p NUMBER_OF_PROCESSES
```

The inspector creates a log file named inspector.log in the logs directory.

### Contract Inspector

The contract_inspector package is used to inspect a given set of contract addresses for their ETH balance, recent
transactions, and internal transactions.
It first fetches the list of all running RPC endpoints from erigon_sorted_hosts.csv file.
Then it starts up a number of processes to inspect contracts in parallel.
Each process then runs several threads to inspect the contract transactions.
The results are then stored in the PostgreSQL database.
Each entry of the database has the following fields:

1. contract_address: The address of the contract
2. balance: The ETH balance of the contract
3. history: The history of the contract transactions
4. internal_transactions: The internal transactions of the contract
5. last_update: The block number of the last update of the contract

In order to inspect a given set of contracts, run the following command:

```bash
  python inspect_many.py -mc PATH_TO_CONTRACTS_CSV_FILE -p NUMBER_OF_PROCESSES
```

