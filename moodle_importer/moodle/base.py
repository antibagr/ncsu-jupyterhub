import typing as t

import requests
from requests.models import Response

from .exceptions import MoodleAPIException
from .response import FluidResponse
from .utils import dump_json

from .typehints import JsonType


class BaseAPIClient:
    '''
    Moodle webservice interface.
    Based on gist of https://gist.github.com/kaqfa
    '''

    DEFAULT_ENDPOINT: str = '/webservice/rest/server.php'

    def __init__(self, key: str, url: str, endpoint: t.Optional[str] = None):
        self.key = key
        self.url = url
        self.endpoint: str = endpoint or self.DEFAULT_ENDPOINT

    def rest_api_parameters(
                self,
                in_args: t.Union[t.Sequence, t.Dict],
                prefix: t.Optional[str] = '',
                out_dict: t.Optional[t.Dict] = None,
            ) -> JsonType:
        '''

        Transform dictionary/array structure to a flat dictionary, with key names
        defining the structure.

        Example usage:

        >>> rest_api_parameters({'courses':[{'id': 1,'name': 'course1'}]})

        {
            'courses[0][id]': 1,
            'courses[0][name]':'course1'
        }

        '''
        if out_dict is None:
            out_dict = {}

        if not isinstance(in_args, (list, dict)):
            out_dict[prefix] = in_args
            return out_dict

        prefix += '{0}' if not prefix else '[{0}]'

        sequence = enumerate(in_args) if isinstance(
            in_args, list) else in_args.items()

        for idx, item in sequence:
            self.rest_api_parameters(item, prefix.format(idx), out_dict)

        return out_dict

    def call(self, fname: str, **kwargs: t.Any) -> FluidResponse:
        '''
        Calls moodle API function with function name fname and keyword arguments.

        Example:
        >>> call_mdl_function('core_course_update_courses',
                               courses = [{'id': 1, 'fullname': 'My favorite course'}])
        '''

        parameters = self.rest_api_parameters(kwargs)

        print(f'''
        Calling "{fname}"

        {dump_json(parameters)[1:-1] or 'Without parameters'}
        '''
              )

        parameters.update({
                        'wstoken': self.key,
                        'moodlewsrestformat': 'json',
                        'wsfunction': fname,
                       })

        resp: Response = requests.post(self.url + self.endpoint, parameters)

        resp.raise_for_status()

        resp_json = FluidResponse(resp)

        if isinstance(resp_json, dict) and 'exception' in resp_json:
            raise MoodleAPIException(resp_json)

        return resp_json

    '''
    Just for usage examples:
    '''

    def example_create_user(self, email, username, password, first_name='-', last_name='-'):
        data = [{'username': username, 'email': email,
                 'password': password, 'firstname': first_name,
                 'lastname': last_name}
                ]

        user = self.call('core_user_create_users', users=data)

        return user

    def example_get_user_by(self, key, value):
        criteria = [{'key': key, 'value': value}]

        user = self.call('core_user_get_users', criteria=criteria)

        return user

    def example_enroll_user_to_course(self, user_id, course_id, role_id=5):
        # 5 is student

        data = [{'roleid': role_id, 'userid': user_id,  'courseid': course_id}]

        enrolment = self.call('enrol_manual_enrol_users', enrolments=data)

        return enrolment

    def example_get_quiz_attempt(self, quiz_id, user_id):
        attempts = self.call('mod_quiz_get_user_attempts',
                             quizid=quiz_id, userid=user_id)
        return attempts
