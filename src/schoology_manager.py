import requests
from bs4 import BeautifulSoup


def login(url: str, username: str, password: str) -> requests.Session:
    """
    Log in to Schoology using requests.

    :param url: The login page URL.
    :param username: The username for login.
    :param password: The password for login.
    :return: A requests.Session object that is logged in.
    """

    if url is None:
        url = 'https://laketravis.schoology.com/'

    session: requests.Session = requests.Session()
    
    response: requests.Response = session.get(url)
    redirect_url: str = response.url
    soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')

    form_build_id: str = soup.find('input', {'name': 'form_build_id'})['value']
    form_id: str = soup.find('input', {'name': 'form_id'})['value']
    school_nid: str = soup.find('input', {'name': 'school_nid'})['value']

    login_data = {
        'mail': username,
        'pass': password,
        'school_nid': school_nid,
        'form_build_id': form_build_id,
        'form_id': form_id,
    }

    response: requests.Response = session.post(redirect_url, data=login_data)
    
    return session


def get_courses(session: requests.Session, url: str) -> list[dict]:
    """
    Get the courses from the Schoology API.

    :param session: The logged-in session.
    :param url: The base URL for the Schoology API.
    :return: A list of dictionaries containing course information.
    """

    course_info: dict = session.get(f'{url}iapi/course/active').json()
    body: dict = course_info.get('body')
    courses: dict = body.get('courses')
    sections: list[dict] = courses.get('sections')

    if sections is None:
        return []
    
    return sections


def find_latin_courses(courses: list[dict]) -> list[dict]:
    """
    Find the Latin courses in the list of courses.

    :param courses: List of courses to search.
    :return: List of Latin courses.
    """

    latin_courses: list[dict] = []

    for course in courses:
        if 'latin' in course.get('section_title').lower():
            latin_courses.append(course)
    
    return latin_courses