from bs4 import BeautifulSoup
import re
import os
import csv
import unittest
import requests  # kept for extra credit parity

# IMPORTANT NOTE:
"""
If you are getting "encoding errors" while trying to open, read, or write from a file, add the following argument to any of your open() functions:
    encoding="utf-8-sig"
"""

def load_listing_results(html_path) -> list[tuple]:
    """
    Load file data from html_path and parse through it to find listing titles and listing ids.
 
    Args:
        html_path (str): The path to the HTML file containing the search results
 
    Returns:
        list[tuple]: A list of tuples containing (listing_title, listing_id)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    with open(html_path, encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, 'html.parser')
 
    results = []
    seen = set()
 
    for a in soup.find_all('a', href=re.compile(r'/rooms/(?:plus/)?\d+')):
        href = a.get('href', '')
        id_match = re.search(r'/rooms/(?:plus/)?(\d+)', href)
        if not id_match:
            continue
        listing_id = id_match.group(1)
 
        if listing_id in seen:
            continue
        seen.add(listing_id) 
        parent = a.parent
        title_tag = parent.find(attrs={'data-testid': 'listing-card-title'})
        if title_tag:
            title = title_tag.get_text(strip=True)
            results.append((title, listing_id))
 
    return results
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================

def get_listing_details(listing_id) -> dict:
    """
    Parse through listing_<id>.html to extract listing details.
 
    Args:
        listing_id (str): The listing id of the Airbnb listing
 
    Returns:
        dict: Nested dictionary in the format:
        {
            "<listing_id>": {
                "policy_number": str,
                "host_type": str,
                "host_name": str,
                "room_type": str,
                "location_rating": float
            }
        }
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    base_dir = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(base_dir, "html_files", f"listing_{listing_id}.html")
 
    with open(path, encoding="utf-8-sig") as f:
        soup = BeautifulSoup(f, 'html.parser')
 
    text = soup.get_text(' ', strip=True)
 
    pol_match = re.search(r'Policy number[:\s]*(\S+)', text, re.IGNORECASE)
    if pol_match:
        raw = pol_match.group(1).strip().rstrip('.')
        raw = re.sub(r'[\ufeff\u200b\r\n]', '', raw)
        if re.search(r'pending', raw, re.IGNORECASE):
            policy_number = "Pending"
        elif re.search(r'exempt', raw, re.IGNORECASE):
            policy_number = "Exempt"
        else:
            policy_number = raw
    else:
        policy_number = "Pending"
 
    host_type = "Superhost" if "Superhost" in text else "regular"
 

    host_name = ""
    room_type = "Entire Room"
 
    for h2 in soup.find_all('h2'):
        h2_text = h2.get_text(strip=True)
        m = re.search(r'hosted by\s+(.+)', h2_text, re.IGNORECASE)
        if m:
            raw_name = m.group(1).replace('\xa0', ' ').strip()
            host_name = raw_name
 
            # Determine room type from the subtitle text
            lower = h2_text.lower()
            if 'private' in lower:
                room_type = "Private Room"
            elif 'shared' in lower:
                room_type = "Shared Room"
            else:
                room_type = "Entire Room"
            break
 
    if not host_name:

        m = re.search(
            r'(?:entire|private|shared)?[\w\s]*hosted by\s+([\w\s&]+?)'
            r'(?:\s+\d+\s+guests|\s+Joined|\s+[\d]+\.\d)',
            text, re.IGNORECASE
        )
        if m:
            raw_name = m.group(1).replace('\xa0', ' ').strip()
            host_name = raw_name
 
        m2 = re.search(r'(private|shared|entire)\s+\w+\s+(?:in\s+\w+\s+)?hosted by',
                       text, re.IGNORECASE)
        if m2:
            keyword = m2.group(1).lower()
            if keyword == 'private':
                room_type = "Private Room"
            elif keyword == 'shared':
                room_type = "Shared Room"
            else:
                room_type = "Entire Room"
 
    loc_match = re.search(r'Location\s+([\d.]+)', text)
    location_rating = float(loc_match.group(1)) if loc_match else 0.0
 
    return {
        listing_id: {
            "policy_number": policy_number,
            "host_type": host_type,
            "host_name": host_name,
            "room_type": room_type,
            "location_rating": location_rating
        }
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================
 
 
def create_listing_database(html_path) -> list[tuple]:
    """
    Use prior functions to gather all necessary information and create a database of listings.
 
    Args:
        html_path (str): The path to the HTML file containing the search results
 
    Returns:
        list[tuple]: A list of tuples. Each tuple contains:
        (listing_title, listing_id, policy_number, host_type, host_name, room_type, location_rating)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    listings = load_listing_results(html_path)
    result = []
 
    for listing_title, listing_id in listings:
        details = get_listing_details(listing_id)
        d = details[listing_id]
        result.append((
            listing_title,
            listing_id,
            d["policy_number"],
            d["host_type"],
            d["host_name"],
            d["room_type"],
            d["location_rating"]
        ))
 
    return result
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================
 
 
def output_csv(data, filename) -> None:
    """
    Write data to a CSV file with the provided filename.
 
    Sort by Location Rating (descending).
 
    Args:
        data (list[tuple]): A list of tuples containing listing information
        filename (str): The name of the CSV file to be created and saved to
 
    Returns:
        None
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    sorted_data = sorted(data, key=lambda row: row[6], reverse=True)
 
    with open(filename, 'w', newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Listing Title", "Listing ID", "Policy Number",
            "Host Type", "Host Name", "Room Type", "Location Rating"
        ])
        for row in sorted_data:
            writer.writerow(row)
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================
 
 
def avg_location_rating_by_room_type(data) -> dict:
    """
    Calculate the average location_rating for each room_type.
 
    Excludes rows where location_rating == 0.0 (meaning the rating
    could not be found in the HTML).
 
    Args:
        data (list[tuple]): The list returned by create_listing_database()
 
    Returns:
        dict: {room_type: average_location_rating}
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    totals = {}
    counts = {}
 
    for row in data:
        room_type = row[5]
        rating = row[6]
        if rating == 0.0:
            continue
        totals[room_type] = totals.get(room_type, 0.0) + rating
        counts[room_type] = counts.get(room_type, 0) + 1
 
    return {
        room_type: round(totals[room_type] / counts[room_type], 2)
        for room_type in totals
    }
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================
 
 
def validate_policy_numbers(data) -> list[str]:
    """
    Validate policy_number format for each listing in data.
    Ignore "Pending" and "Exempt" listings.
 
    Args:
        data (list[tuple]): A list of tuples returned by create_listing_database()
 
    Returns:
        list[str]: A list of listing_id values whose policy numbers do NOT match the valid format
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    valid_pattern = re.compile(r'^(20\d{2}-00\d{4}STR|STR-000\d{4})$')
 
    invalid_ids = []
    for row in data:
        listing_id = row[1]
        policy = row[2]
 
        if policy in ("Pending", "Exempt"):
            continue
 
        if not valid_pattern.match(policy):
            invalid_ids.append(listing_id)
 
    return invalid_ids
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================
 
 
# EXTRA CREDIT
def google_scholar_searcher(query):
    """
    EXTRA CREDIT
 
    Args:
        query (str): The search query to be used on Google Scholar
    Returns:
        List of titles on the first page (list)
    """
    # ==============================
    # YOUR CODE STARTS HERE
    # ==============================
    url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
 
    titles = []
    for tag in soup.find_all('h3', class_='gs_rt'):
        title_text = tag.get_text(strip=True)
        title_text = re.sub(r'^\[(PDF|HTML|BOOK|CITATION)\]\s*', '', title_text)
        titles.append(title_text)
 
    return titles
    # ==============================
    # YOUR CODE ENDS HERE
    # ==============================
 
 
class TestCases(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.search_results_path = os.path.join(self.base_dir, "html_files", "search_results.html")
 
        self.listings = load_listing_results(self.search_results_path)
        self.detailed_data = create_listing_database(self.search_results_path)
 
    def test_load_listing_results(self):
        self.assertEqual(len(self.listings), 18)
 
        self.assertEqual(self.listings[0], ("Loft in Mission District", "1944564"))
 
    def test_get_listing_details(self):
        html_list = ["467507", "1550913", "1944564", "4614763", "6092596"]
 
        results = [get_listing_details(lid) for lid in html_list]
 
        self.assertEqual(results[0]["467507"]["policy_number"], "STR-0005349")
 
        self.assertEqual(results[2]["1944564"]["host_type"], "Superhost")
        self.assertEqual(results[2]["1944564"]["room_type"], "Entire Room")
 
        self.assertEqual(results[2]["1944564"]["location_rating"], 4.9)
 
    def test_create_listing_database(self):
        for tup in self.detailed_data:
            self.assertEqual(len(tup), 7)
 
        self.assertEqual(
            self.detailed_data[-1],
            ("Guest suite in Mission District", "467507", "STR-0005349",
             "Superhost", "Jennifer", "Entire Room", 4.8)
        )
 
    def test_output_csv(self):
        out_path = os.path.join(self.base_dir, "test.csv")
 
        output_csv(self.detailed_data, out_path)
 
        with open(out_path, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
 
        self.assertEqual(
            rows[1],
            ["Guesthouse in San Francisco", "49591060", "STR-0000253",
             "Superhost", "Ingrid", "Entire Room", "5.0"]
        )
 
        os.remove(out_path)
 
    def test_avg_location_rating_by_room_type(self):
        avgs = avg_location_rating_by_room_type(self.detailed_data)
 
        self.assertEqual(avgs["Private Room"], 4.9)
 
    def test_validate_policy_numbers(self):
        invalid_listings = validate_policy_numbers(self.detailed_data)
 
        self.assertEqual(invalid_listings, ["16204265"])
 
 
def main():
    detailed_data = create_listing_database(os.path.join("html_files", "search_results.html"))
    output_csv(detailed_data, "airbnb_dataset.csv")
 
 
if __name__ == "__main__":
    main()
    unittest.main(verbosity=2)
 