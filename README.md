# Cryptovote

6.857 final project on homomorphic encryption for voting systems

## Installation

Requires Python 3.6+.

```bash
git clone https://github.com/swansonk14/crypto-voting.git
cd crypto-voting
pip install -e cryptovote
```
*Note that the `-e` flag will instruct pip to install the package as "editable". That is, when changes are made to any part of the package during development, those changes will immediately be available system-wide on the activated python environment.*

All requirements for this package should be added to `setup.py`.

## Web Interface

To run an election via the web interface, run the following commands:

```bash
cd cryptovote_web
pip install -r requirements.txt
python -m flask run
```

Prior to initially running the web interface, the file `.env.example` should be copied into a new file named `.env` with the desired values set. Also note that Chrome seems to be the only browser that supports DNS resolution for subdomains of the localhost, so for development Chrome must be used for portions of the site that use subdomains. Finally, if actually deployed on a non-localhost server HTTPS must be used in order for WebAuthn to work.

## Real Election Data

San Francisco voting data from the November 2016 election is available in the `data` directory ([source](https://www.rankedchoicevoting.org/data_clearinghouse)). The script for converting the San Francisco ballot image data to our CandidateOrderBallot format is in `scripts/load_ballot_data.py`. It can be run with:

```bash
python scripts/load_ballot_data.py --master_lookup data/san_francisco_nov_2016_master_lookup.txt --ballot_image data/san_francisco_nov_2016_ballot_image.txt
```

## Acknowledgements

This package is an implementation of the ShuffleSum algorithm proposed [in this paper](https://talmoran.net/papers/BMNRT09-shuffle-sum.pdf?fbclid=IwAR0jZ18H2ZYMsCjPkW-3ohDNom5UjbK-jMen6_lISVoWJJnPWM0A41KAS1Y)
