import json

from moodle import errors
from .senders import LTI13GradeSender
from tornado import web

from jupyterhub.handlers import BaseHandler


class SendGradesHandler(BaseHandler):
    '''
    Defines a POST method to process grades submission
    for a specific assignment within a course
    '''

    async def post(self, course_id: str, assignment_name: str) -> None:
        '''
        Receives a request with the course name and the assignment name as path parameters
        which then uses the appropriate class to send grades to the platform based on the
        LTI authenticator version (1.1 or 1.3).

        Arguments:
          course_id: course name which has been previously normalized by the LTIUtils.normalize_string
            function.
          assignment_name: assignment name which should coincide with the assignment name within the LMS.

        Raises:
          GradesSenderCriticalError if there was a critical error when either extracting grades from the db
            or sending grades to the tool consumer / platform.
          AssignmentWithoutGradesError if the assignment does not have any grades associated to it.
          GradesSenderMissingInfoError if ther is missing information when attempting to send grades.
        '''

        self.log.debug(
            f'Data received to send grades-> course:{course_id}, assignment:{assignment_name}'
        )

        lti_grade_sender = LTI13GradeSender(course_id, assignment_name)

        try:
            await lti_grade_sender.send_grades()

        except errors.GradesSenderCriticalError as exc:
            raise web.HTTPError(
                400, 'There was an critical error, please check logs.') from exc

        except errors.AssignmentWithoutGradesError as exc:
            raise web.HTTPError(
                400, 'There are no grades yet to submit') from exc

        except errors.GradesSenderMissingInfoError as exc:

            self.log.error(f'There are missing values.{exc}')

            raise web.HTTPError(
                400,
                'Impossible to send grades. There are missing values, please check logs. {str(exc)}',
            ) from exc

        except Exception as exc:
            raise web.HTTPError(400, str(exc)) from exc

        self.write(json.dumps({'success': True}))
