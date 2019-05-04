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
cd cryptovote-web
pip install -r requirements.txt
python -m flask run
```

Prior to initially running the web interface, the file `.env.example` should be copied into a new file named `.env` with the desired values set. Also note that for the portions of the site that use subdomains, you will need to either hardcode subdomain redirects into your system's host file or follow [this tutorial](https://passingcuriosity.com/2013/dnsmasq-dev-osx/) because subdomain resolution is only supported for TLDs. If you follow this tutorial, pick something other than `.dev`, as recent updates in Chrome and Firefox break that GTLD over HTTP. Finally, you will have to manually specify the hostname you have chosen within your `.env` configuration file:

## Acknowledgements

This package is an implementation of the ShuffleSum algorithm proposed [in this paper](https://talmoran.net/papers/BMNRT09-shuffle-sum.pdf?fbclid=IwAR0jZ18H2ZYMsCjPkW-3ohDNom5UjbK-jMen6_lISVoWJJnPWM0A41KAS1Y)
