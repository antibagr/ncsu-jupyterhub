# import os
from moodle import Moodle, FileGenerator  # type: ignore
# from moodle.utils import dump_json

URL = "https://rudie.moodlecloud.com"
KEY = "0461b4a7e65e63921172fa3727f0863c"


client = Moodle(KEY, URL)

# client.sync()

gen = FileGenerator()

gen.generate()

#
# # resp = client.call('core_user_get_users_by_field', field='email', values=['*',])
#
# # resp = client.call('core_enrol_get_enrolled_users', courseid=5)
#
# # client.list_users()
#
# # courses = []
# #
# # for course in client.get_courses():
# #     courses.append({
# #             'id': course['id'],
# #             'title': course['displayname'],
# #             'short_name': course['shortname'],
# #             'instructors': [],
# #             'students': [],
# #             'graders': [],
# #         })
# #
# # print(courses)
#
# courses = [{'id': 1, 'title': 'My new Moodle site', 'short_name': 'Your School', 'instructors': [], 'students': [], 'graders': []}, {'id': 6, 'title': 'Second Course', 'short_name': 'second_course',
#                                                                                                                                               'instructors': [], 'students': [], 'graders': []}, {'id': 5, 'title': 'First Course', 'short_name': 'first_course', 'instructors': [], 'students': [], 'graders': []}]
#
# users = {}
#
# all_roles = ('student', 'teaching_assistant', 'teacher',
#              'instructional_support', 'editingteacher', 'manager', 'coursecreator')
#
# role_priority = {k: v for k, v in zip(all_roles, range(len(all_roles)))}
#
# role_priority_reversed = {v: k for k, v in role_priority.items()}
#
#
# def priority(role: str, reversed: bool = False) -> int:
#     return role_priority[role] if not reversed else role_priority_reversed[role]
#
#
# for course in courses:
#
#     course_users = client.get_users(course['id'])
#
#     for user in course_users:
#
#         course_user = {
#             'id': user['id'],
#             'first_name': user['firstname'],
#             'last_name': user['lastname'],
#             'username': user['username'],
#             'email': user['email'],
#         }
#
#         if user['email'] not in users:
#             users[user['email']] = course_user
#
#         if user['roles']:
#
#             role_rate = max([priority(role['shortname'])
#                              for role in user['roles']])
#
#             course_user['role'] = priority(role_rate, reversed=True)
#
#             if course_user['role'] == 'student':
#                 group = 'students'
#             elif course_user['role'] in ('editingteacher', 'manager', 'coursecreator'):
#                 group = 'instructors'
#             else:
#                 group = 'graders'
#
#             course[group].append(course_user)
#
# with open(os.path.join(os.path.dirname(__file__), 'data', 'courses.json'), 'w') as f:
#     f.write(dump_json(courses))
#
# print(dump_json(courses))
