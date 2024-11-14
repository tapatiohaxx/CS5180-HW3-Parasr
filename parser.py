from bs4 import BeautifulSoup
from pymongo import MongoClient
import requests

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017/')
db = client['cs_department']
professors_collection = db.professors

def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_faculty_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    faculty_divs = soup.find_all('div', class_='clearfix')  # Based on the HTML structure you provided
    for div in faculty_divs:
        try:
            name = div.h2.text.strip() if div.h2 else None
            details = div.find_all('p')
            title, office, phone, email, web = None, None, None, None, None
            for detail in details:
                text = detail.text
                if 'Title:' in text:
                    title = text.split('Title:')[-1].strip()
                if 'Office:' in text:
                    office = text.split('Office:')[-1].strip()
                if 'Phone:' in text:
                    phone = text.split('Phone:')[-1].strip()
                if 'Email:' in text:
                    email = detail.find('a').get_text().strip()
                if 'Web:' in text:
                    web = detail.find('a')['href'].strip()

            professor_data = {
                'name': name,
                'title': title,
                'office': office,
                'phone': phone,
                'email': email,
                'website': web
            }
            store_faculty_data(professor_data)
        except Exception as e:
            print(f"Error processing faculty data for {name}: {e}")

def store_faculty_data(faculty_data):
    if faculty_data:
        result = professors_collection.insert_one(faculty_data)
        print(f"Data inserted for {faculty_data['name']}, MongoDB ID: {result.inserted_id}")
    else:
        print("No data to insert.")

if __name__ == "__main__":
    url = 'https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml'
    html_content = fetch_html(url)
    if html_content:
        parse_faculty_data(html_content)
    else:
        print("Failed to retrieve content.")
