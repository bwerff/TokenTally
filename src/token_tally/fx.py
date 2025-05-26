import urllib.request
from xml.etree import ElementTree

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
INTRADAY_URL = "https://example.com/fx/intraday.xml"


def parse_ecb_rates(xml_data: bytes) -> dict:
    """Parse ECB FX XML into a currency->rate mapping (EUR base)."""
    tree = ElementTree.fromstring(xml_data)
    ns = {
        "gesmes": "http://www.gesmes.org/xml/2002-08-01",
        "ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
    }
    cube = tree.find(".//ecb:Cube/ecb:Cube", ns)
    rates = {"EUR": 1.0}
    if cube is not None:
        for child in cube:
            cur = child.attrib.get("currency")
            rate = child.attrib.get("rate")
            if cur and rate:
                rates[cur] = float(rate)
    return rates


def get_ecb_rates() -> dict:
    """Fetch the latest FX rates from ECB."""
    with urllib.request.urlopen(ECB_URL) as resp:
        data = resp.read()
    return parse_ecb_rates(data)


def get_intraday_rates() -> dict:
    """Fetch intraday FX rates from the alternate feed."""
    with urllib.request.urlopen(INTRADAY_URL) as resp:
        data = resp.read()
    return parse_ecb_rates(data)


def convert(amount: float, from_cur: str, to_cur: str, rates: dict) -> float:
    """Convert an amount between currencies using EUR-based rates."""
    if from_cur not in rates or to_cur not in rates:
        raise ValueError("Missing currency rate")
    eur = amount / rates[from_cur]
    return eur * rates[to_cur]
