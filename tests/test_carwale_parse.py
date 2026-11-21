import pytest

pytest.importorskip("playwright")        # site_carwale imports playwright; skip where it is not installed

from scraper import site_carwale as cw  # noqa: E402

BASE = "https://www.carwale.com/used/"
NB = "\xa0\xa0|\xa0\xa0"                  # CarWale separates the fields with non-breaking spaces and bars

# real card titles copied from the live site (no price in them)
REAL = [
    ("2019 Maruti Suzuki Swift VXi AMT\n39,000 km" + NB + "Petrol" + NB + "Andheri-Kurla Road, Mumbai",
     "mumbai/maruti-suzuki-swift/rdmaoog9/", (2019, "Maruti Suzuki", "Swift", "Petrol", 39000, "Andheri-Kurla Road, Mumbai")),
    ("2009 Maruti Suzuki Swift VDi\n1,35,242 km" + NB + "Diesel" + NB + "Basapura, Bangalore",
     "bangalore/maruti-suzuki-swift/5c41dkg7/", (2009, "Maruti Suzuki", "Swift", "Diesel", 135242, "Basapura, Bangalore")),
    ("2014 Maruti Suzuki Swift VXi [2014-2017]\n44,000 km" + NB + "Petrol + 1" + NB + "Multani Mohalla, Delhi",
     "delhi/maruti-suzuki-swift/otsv6jsf/", (2014, "Maruti Suzuki", "Swift", "Petrol", 44000, "Multani Mohalla, Delhi")),
    ("2025 Maruti Suzuki Swift ZXi Plus Petrol Automatic (AMT) Dual Tone [2024-2026]\n25,994 km" + NB + "Petrol" + NB + "Dombivli, Thane",
     "thane/maruti-suzuki-swift/ap7f5e8g/", (2025, "Maruti Suzuki", "Swift", "Petrol", 25994, "Dombivli, Thane")),
    ("2012 Maruti Suzuki Swift LXi Petrol Manual [2024-2026]\n72,000 km" + NB + "Petrol" + NB + "Varuna Bridge,Varanasi Cantt, Varanasi",
     "varanasi/maruti-suzuki-swift/n8s3vnod/", (2012, "Maruti Suzuki", "Swift", "Petrol", 72000, "Varuna Bridge,Varanasi Cantt, Varanasi")),
    ("2018 Maruti Suzuki Swift ZXi AMT [2018-2019]\n16,000 km" + NB + "Petrol" + NB + "Chembur, Mumbai",
     "mumbai/maruti-suzuki-swift/223926c714b5495a86c06f00fb938fc3/", (2018, "Maruti Suzuki", "Swift", "Petrol", 16000, "Chembur, Mumbai")),
]


@pytest.mark.parametrize("title,path,expected", REAL)
def test_real_titles_with_price_found_elsewhere_on_the_card(title, path, expected):
    card = title + "\n₹ 6.35 Lakh\nEMI ₹ 11,200/month\nBook test drive"
    row = cw.parse_card(title, BASE + path, card)
    year, brand, model, fuel, km, location = expected
    assert (row["year"], row["brand"], row["model"], row["fuel_type"], row["km_driven"], row["location"]) == \
        (year, brand, model, fuel, km, location)
    assert row["price"] == 635000


def test_no_price_anywhere_means_not_parsed():
    title = REAL[0][0]
    assert cw.parse_card(title, BASE + REAL[0][1], title + "\nBook test drive") is None


@pytest.mark.parametrize("text,expected", [
    ("₹ 6.35 Lakh", 635000),
    ("Rs. 17.75 Lakh", 1775000),
    ("₹ 1.05 Crore", 10500000),
    ("₹ 5.89 Lakh ₹ 6.20 Lakh", 589000),        # old struck-through price next to the current one
    ("₹ 85,000", 85000),
    ("₹ 4.5 Lakh  EMI ₹ 9,500/month", 450000),
    ("EMI ₹ 9,500/month", None),                    # an EMI is not a price
    ("", None),
    (None, None),
])
def test_find_price(text, expected):
    assert cw.find_price(text) == expected


def test_old_layout_with_price_after_the_location_still_works():
    row = cw.parse_card("2024 Toyota Urban Cruiser Hyryder G Hybrid [2023-2025] 24,800 km | Petrol | Makarba, Ahmedabad Rs. 17.75 Lakh",
                        BASE + "ahmedabad/toyota-urban-cruiser-hyryder/ab12cd/")
    assert row["price"] == 1775000 and row["location"] == "Makarba, Ahmedabad" and row["fuel_type"] == "Hybrid"


def test_records_to_rows_uses_the_card_text_and_the_card_photo():
    href = BASE + REAL[0][1]
    recs = [
        {"href": href, "text": "", "card": "", "img": "", "alt": ""},                                  # e.g. the photo link
        {"href": href, "text": REAL[0][0], "card": REAL[0][0] + "\n₹ 6.35 Lakh", "img": "https://imgd.aeplcdn.com/x.jpg", "alt": "Swift"},
    ]
    rows, unparsed = cw.records_to_rows({href: recs})
    assert unparsed == [] and rows[0]["price"] == 635000 and rows[0]["url"] == href
    assert rows[0]["image_url"] == "https://imgd.aeplcdn.com/x.jpg"


def test_unparsed_report_shows_title_and_card_text():
    href = BASE + REAL[0][1]
    rows, unparsed = cw.records_to_rows({href: [{"href": href, "text": REAL[0][0], "card": "no price here", "img": "", "alt": ""}]})
    assert rows == [] and "CARD:" in unparsed[0][1] and "no price here" in unparsed[0][1]


# ---- choosing the car photo from everything on a card ---------------------------------------------

@pytest.mark.parametrize("src,expected", [
    ("https://imgd.aeplcdn.com/664x374/n/swift.jpg", "https://imgd.aeplcdn.com/664x374/n/swift.jpg"),
    ("//imgd.aeplcdn.com/n/swift.webp", "https://imgd.aeplcdn.com/n/swift.webp"),
    ("data:image/gif;base64,R0lGOD", None),
    ("https://imgd.aeplcdn.com/grey-placeholder.png", None),
    ("https://cdn.example/brand-logo.png", None),
    ("https://cdn.example/icons/star.svg", None),
    ("/relative/path.jpg", None),
    ("", None),
    (None, None),
])
def test_clean_image_url(src, expected):
    assert cw.clean_image_url(src) == expected


def test_choose_image_prefers_the_biggest_real_photo():
    pics = [
        {"src": "https://imgd.aeplcdn.com/grey-placeholder.png", "alt": "", "w": 310, "h": 174},    # lazy placeholder
        {"src": "https://imgd.aeplcdn.com/icons/certified-badge.png", "alt": "", "w": 40, "h": 40},  # badge
        {"src": "https://imgd.aeplcdn.com/310x174/n/a.jpg", "alt": "Swift", "w": 310, "h": 174},
        {"src": "https://imgd.aeplcdn.com/80x45/n/b.jpg", "alt": "thumb", "w": 80, "h": 45},        # too small
    ]
    assert cw.choose_image(pics) == ("https://imgd.aeplcdn.com/310x174/n/a.jpg", "Swift")


def test_choose_image_with_unknown_sizes_and_nothing_usable():
    assert cw.choose_image([{"src": "https://x.com/a.jpg"}]) == ("https://x.com/a.jpg", None)
    assert cw.choose_image([{"src": "data:image/png;base64,AAAA", "w": 300, "h": 200}]) == (None, None)
    assert cw.choose_image([]) == (None, None)


def test_records_to_rows_takes_the_photo_from_the_lazy_attribute():
    href = BASE + REAL[0][1]
    rec = {"href": href, "text": REAL[0][0], "card": REAL[0][0] + "\n₹ 6.35 Lakh", "imgs": [
        {"src": "https://imgd.aeplcdn.com/grey-placeholder.png", "alt": "", "w": 310, "h": 174},
        {"src": "https://imgd.aeplcdn.com/310x174/n/swift-1.jpg", "alt": "Swift", "w": 310, "h": 174}]}
    rows, _ = cw.records_to_rows({href: [rec]})
    assert rows[0]["image_url"] == "https://imgd.aeplcdn.com/310x174/n/swift-1.jpg" and rows[0]["image_alt"] == "Swift"
