import json
import os
import re
import typing as t
from datetime import datetime

from loguru import logger
from custom_inherit import DocInheritMeta
from tornado.httpclient import AsyncHTTPClient
from nbgrader.api import Course, Gradebook, MissingEntry

from moodle.helper import NBGraderHelper
from moodle.errors import (AssignmentWithoutGradesError,
                           GradesSenderCriticalError,
                           GradesSenderMissingInfoError)
from moodle.lti13.auth import get_lms_access_token

from moodle.utils import dump_json


class GradesBaseSender(metaclass=DocInheritMeta(style='google_with_merge', include_special_methods=True)):
    '''
    This class helps to send student grades from nbgrader database.
    Classes that inherit from this class must implement
    the send_grades() method.

    Args:
        course_id (str): Course id or name used in nbgrader
        assignment_name (str): Assignment name that needs to be processed
            and from which the grades are retrieved

    Attributes:
        helper (NBGraderHelper): .
        course (Course): .
        all_lineitems (list): .
        headers (dict): .
        course_id (str): .
        assignment_name (str): .

    '''

    def __init__(self, course_id: str, assignment_name: str):
        '''
        Check if required enviroments is set.

        Args:
            course_id (str): .
            assignment_name (str): .

        Raises:
            EnvironmentError: If one of environment variable is not set.

        '''

        envs = ('LTI13_PRIVATE_KEY', 'LTI13_TOKEN_URL', 'LTI13_CLIENT_ID')

        if any(os.environ.get(env) is None for env in envs):
            raise EnvironmentError(', '.join(envs) + ' should be set.')

        self.course_id = course_id
        self.assignment_name = assignment_name

        self.helper = NBGraderHelper()

        self.course = self.helper.get_course(self.course_id)

        self.all_lineitems = []
        self.headers = {}

    async def send_grades(self):
        raise NotImplementedError

    @property
    def grader_name(self) -> str:
        return f'grader-{self.course_id}'

    @property
    def gradebook_dir(self) -> str:
        return f'/home/{self.grader_name}/{self.course_id}'

    def _retrieve_grades_from_db(self) -> t.Tuple[int, t.List[dict]]:
        '''Gets grades from the database'''

        out: t.List[dict] = []

        max_score = 0

        # Create the connection to the gradebook database
        with self.helper.get_db(self.course_id) as gb:

            try:

                # retrieve the assignment record
                assignment_row = gb.find_assignment(self.assignment_name)

                max_score = assignment_row.max_score

                submissions = gb.assignment_submissions(self.assignment_name)

                logger.info(
                    f'Found {len(submissions)} submissions for assignment: {self.assignment_name}'
                )

            except MissingEntry as exc:
                logger.error(f'Assignment not found in database: {exc}')
                raise GradesSenderMissingInfoError(self.course_id) from exc

            for submission in submissions:

                # retrieve the student to use the lms id
                student = gb.find_student(submission.student_id)

                out.append({
                    'score': submission.score,
                    'lms_user_id': student.lms_user_id
                })

        logger.info(f'Grades found: {out}')
        logger.info(f'Maximum score for this assignment {max_score}')

        return max_score, out


class LTI13GradeSender(GradesBaseSender):
    '''
    Creates a new class to help us to send grades
    saved in the nbgrader gradebook (sqlite) back to the LMS

    For simplify the submission we're using the lineitem_id (that is a url)
    obtained in authentication flow and it indicates us where send the scores
    So the assignment item in the database should contains the 'lms_lineitem_id'
    with something like /api/lti/courses/:course_id/line_items/:line_item_id
    '''

    def _get_course(self) -> Course:
        '''
        Gets the course model instance
        '''

        with self.helper.get_db(self.course_id) as gb:

            course = gb.check_course(self.course_id)

            logger.debug(f'course got from db:{course}')

            return course

    def _find_next_url(self, link_header: str) -> t.Optional[str]:
        '''
        Extract the url value from link header value
        '''

        # split the paths
        next_url = (n for n in link_header.split(',') if 'next' in n)

        try:

            next_url = next(next_url)

            logger.debug(f'There are more lineitems in: {next_url}')

            link_regex = re.compile(
                r'((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)',
                re.DOTALL,
            )

            links = re.findall(link_regex, next_url)

            if links:
                return links[0][0]

        except StopIteration:
            ...

    async def _get_lineitems_from_url(self, url: str) -> None:
        '''
        Fetch the lineitems from specific url and add them to general list
        '''

        items = []

        if not url:
            return

        client = AsyncHTTPClient()

        resp = await client.fetch(url, method='GET', headers=self.headers)

        items = json.loads(resp.body)

        if items:

            self.all_lineitems.extend(items)

            headers = resp.headers

            # check if there is more items/pages
            if 'Link' in headers and 'next' in headers['Link']:

                next_url = self._find_next_url(headers['link'])

                await self._get_lineitems_from_url(next_url)

    async def _get_line_item_info_by_assignment_name(self) -> str:
        '''
        Returns JSON.
        '''

        await self._get_lineitems_from_url(self.course.lms_lineitems_endpoint)

        if not self.all_lineitems:

            raise GradesSenderMissingInfoError(
                f'No line-items were detected for this course: {self.course_id}'
            )

        logger.debug(f'LineItems retrieved: {self.all_lineitems}')

        lineitem_matched = None

        for item in self.all_lineitems:

            item_label = item['label']

            if (
                self.assignment_name.lower() == item_label.lower()
                or self.assignment_name.lower()
                == self.helper.format_string(item_label)
            ):
                lineitem_matched = item['id']  # the id is the full url
                logger.debug(
                    f'There is a lineitem matched with the assignment {self.assignment_name}. {item}'
                )
                break

        if lineitem_matched is None:
            raise GradesSenderMissingInfoError(
                f'No lineitem matched with the assignment name: {self.assignment_name}'
            )

        logger.info(f'Lineitem is {lineitem_matched}')

        logger.info(f'Item is {item}')

        return item

        # client = AsyncHTTPClient()

        # resp = await client.fetch(item['id'], headers=self.headers)
        #
        # lineitem_info = json.loads(resp.body)
        #
        # logger.debug(f'Fetched lineitem info from lms {lineitem_info}')
        #
        # return lineitem_info

    async def _set_access_token_header(self):
        '''
        Sets header dict of self.
        '''

        token = await get_lms_access_token(
            os.environ.get('LTI13_TOKEN_URL'), os.environ.get(
                'LTI13_PRIVATE_KEY'), os.environ.get('LTI13_CLIENT_ID')
        )

        if 'access_token' not in token:

            logger.info(
                f'response from {os.environ.get("LTI13_TOKEN_URL")}: {token}')

            raise GradesSenderCriticalError(
                'The "access_token" key is missing')

        # set all the headers to use in lms requests
        self.headers = {
          'Authorization': '{token_type} {access_token}'.format(**token),
          'Content-Type': 'application/vnd.ims.lis.v2.lineitem+json',
          'accept': 'application/vnd.ims.lis.v2.lineitemcontainer+json'
        }

    async def send_grades(self) -> None:
        '''
        Send grades to LMS iteratively.
        '''

        _, nbgrader_grades = self._retrieve_grades_from_db()

        if not nbgrader_grades:
            raise AssignmentWithoutGradesError('No grades found.')

        await self._set_access_token_header()

        lineitem_info = await self._get_line_item_info_by_assignment_name()

        score_maximum = lineitem_info['scoreMaximum']

        client = AsyncHTTPClient()

        self.headers['Content-Type'] = 'application/vnd.ims.lis.v1.score+json'

        for grade in nbgrader_grades:

            score = float(grade['score'])
            data = {
                'timestamp': datetime.now().isoformat(),
                'userId': grade['lms_user_id'],
                'scoreGiven': score,
                'scoreMaximum': score_maximum,
                'gradingProgress': 'FullyGraded',
                'activityProgress': 'Completed',
                'comment': '',
            }

            logger.info(f'data used to sent scores: {dump_json(data)}')

            url = lineitem_info['id'].replace('?type_id=1', '') + '/scores'

            logger.debug(f'URL for grades submission {url}')

            await client.fetch(
                url, body=json.dumps(data), method='POST', headers=self.headers
            )
