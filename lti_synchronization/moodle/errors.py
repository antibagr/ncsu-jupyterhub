import typing as t

from loguru import logger
from lxml import etree, html
from requests.exceptions import HTTPError
from requests.models import Response

from moodle.typehints import JsonType
from moodle.utils import dump_json


''' Moodle API exceptions '''


class MoodleHTTPException(HTTPError):
    '''
    Non-success status code received after API Call.
    '''


class MoodleAPIException(ValueError):
    '''
    Exception raises when Moodle API responses with a dictionary
    containing "exception" key or if Moodle API did not return JSON.
    '''

    def __init__(self, resp: t.Union[JsonType, Response]):

        content: str

        if isinstance(resp, Response):

            logger.error(
                'Response received from Moodle cannot be interpreted as JSON.')

            content = etree.tostring(
                html.fromstring(resp.content.decode('utf-8')),
                encoding='unicode',
                pretty_print=True
            )

        else:

            content = dump_json(resp)

        super().__init__(
            'Exception while calling Moodle API:'.center(39, '\n')
            + content
        )


class MoodlePermissionError(PermissionError):
    '''
    Exception raised when a REST API Client does not have permissions to
    function used in call.
    '''

    def __init__(self, function_name: str):
        super().__init__(
            f'Service does not have access to function {function_name!r}.\nConsider adding it in ' \
            'Site administration / Plugins / Web services / External services / Functions\n' \
            'You can list all functions required to be enabled using MoodleClient.functions attribute'
        )


''' Grades sender exceptions '''


class GradesSenderError(Exception):
    '''
    Base class for submission errors
    '''


class GradesSenderCriticalError(GradesSenderError):
    '''
    Error to identify when something critical happened
    In this case, the problem will continue until an admin checks the logs
    '''


class AssignmentWithoutGradesError(GradesSenderError):
    '''
    Error to identify when a submission request was made but there are not yet grades in the gradebook.db
    '''


class GradesSenderMissingInfoError(GradesSenderError):
    '''
    Error to identify when a assignment is not related or associated correctly between lms and nbgrader
    '''
