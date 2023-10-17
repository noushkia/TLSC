# TLSC

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

A tool that finds smart contracts with time locks on Ethereum main-net

## Table of Contents

- [Install](#install)
- [Usage](#usage)
    - [RPC Finder](#rpc-finder)
    - [Inspector](#inspector)
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

### Inspector

The tlsc_inspector package is used to inspect a given range of Ethereum blocks for contracts that have time locks.
It first fetches the list of all running RPC endpoints from erigon_sorted_hosts.csv file.
Then it starts up a number of processes to inspect blocks in parallel.
Each process then runs several threads to fetch blocks from the RPC endpoints and inspect them for the contracts.
The results are then stored in the PostgreSQL database.

In order to inspect a given range of blocks, run the following command:

```bash
  python inspector.py -a START_BLOCK_RANGE -b END_BLOCK_RANGE
```

The inspector by default starts up as many processes as the number of available cpu cores.
You can specify the number of processes to start up by using the -p flag:

```bash
  python inspector.py -a START_BLOCK_RANGE -b END_BLOCK_RANGE -p NUMBER_OF_PROCESSES
```

The inspector creates a log file named inspector.log in the logs directory.

## todo
