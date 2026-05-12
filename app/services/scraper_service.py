from pathlib import Path
import re

import requests
from bs4 import BeautifulSoup

from .medicine_service import upsert_medicine

NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")


def parse_number(value, default=0):
    if value is None:
        return default

    match = NUMBER_PATTERN.search(str(value))
    if not match:
        return default

    number = float(match.group(1))
    return int(number) if number.is_integer() else number


def load_source_html(source):
    if source == "sample":
        sample_path = Path(__file__).resolve().parent.parent / "sample_data" / "medicine_catalog.html"
        return sample_path.read_text(encoding="utf-8"), str(sample_path)

    response = requests.get(source, timeout=15)
    response.raise_for_status()
    return response.text, source


def parse_medicine_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    medicines = []

    for card in soup.select("[data-medicine-card]"):
        name = card.select_one("[data-name]")
        price = card.select_one("[data-price]")
        quantity = card.select_one("[data-quantity]")

        if not name or not price or not quantity:
            continue

        medicines.append(
            {
                "name": name.get_text(strip=True),
                "price": float(parse_number(price.get_text(strip=True), default=0)),
                "quantity": int(parse_number(quantity.get_text(strip=True), default=0)),
            }
        )

    if medicines:
        return medicines

    for row in soup.select("table tr"):
        cells = [cell.get_text(strip=True) for cell in row.select("td")]
        if len(cells) < 3:
            continue

        medicines.append(
            {
                "name": cells[0],
                "price": float(parse_number(cells[1], default=0)),
                "quantity": int(parse_number(cells[2], default=0)),
            }
        )

    return [medicine for medicine in medicines if medicine["name"]]


def scrape_and_import_medicines(source="sample"):
    html, resolved_source = load_source_html(source)
    medicines = parse_medicine_cards(html)

    if not medicines:
        raise ValueError("No medicines found in the provided source.")

    imported = 0
    for medicine in medicines:
        upsert_medicine(
            name=medicine["name"],
            quantity=medicine["quantity"],
            price=medicine["price"],
        )
        imported += 1

    return {"count": imported, "source": resolved_source}
