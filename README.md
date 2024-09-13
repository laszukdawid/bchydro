# BCHydro

BCHydro Python API for extracting electricity usage statistics from your personal account.

## Installation

Checkout repo and use it.

```sh
# Fetch the code
git clone https://github.com/laszukdawid/bchydro.git
cd bchydro

```

Recommended method of executing common commands is via [Taskfile](https://taskfile.dev/).

```sh
# Create virtual environment via venv
task venv
# or
uv venv
```

*Note* that this is my first `uv` repo, ... so, be cautious.

## Usage

Provided script is a browser scraper via Playwright. A part of usage is logging in.
For this, you need to set credentials. Either set them as a enviroment variables, or create `.env` file with them.

To set env variables and execute scraping:

```sh
export BCH_USER=your.email@domain.com
export BCH_PASS=your-bch-password

task run
```

## Acknowledge

This project started out as a fork of https://github.com/emcniece/bchydro/. However, I started modifying too much and eventually removed everything. There's little code left from the previous repo, but memory and gratitude persisted.

## Disclaimer

This project has been developed without the express permission of BC Hydro. It accesses data by submitting forms that end-users would typically use in a browser. I'd love to work with BC Hydro to find a better way to access this data, perhaps through an official API... if you know anyone that works there, pass this along!
