import typing as t
import json

from moodle.typehints import JsonType, Course, User

''' Function utils '''


def dump_json(dict_in: JsonType) -> str:
    '''
    Dump json-like dictionary to string with indentation.
    '''

    return json.dumps(dict_in, indent=4, sort_keys=True, ensure_ascii=False)


def format_course(course: dict) -> Course:
    '''
    Format raw json response to convinient dictionary.
    '''

    return {
            'id': course['id'],
            'title': course['displayname'],
            'short_name': course['shortname'],
            'instructors': [],
            'students': [],
            'graders': [],
    }

def format_user(user: dict) -> User:
    '''
    Format raw json response to convinient dictionary.
    '''

    return {
        'id': user['id'],
        'first_name': user['firstname'],
        'last_name': user['lastname'],
        'username': user['username'],
        'email': user['email'],
        'roles': [role['shortname'] for role in user['roles']],
    }
