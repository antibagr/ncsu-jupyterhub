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
