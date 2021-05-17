from moodle import Moodle  # type: ignore

URL = "https://rudie.moodlecloud.com"
KEY = "0461b4a7e65e63921172fa3727f0863c"


client = Moodle(KEY, URL)

# resp = client.call('core_user_get_users_by_field', field='email', values=['*',])

# resp = client.call('core_enrol_get_enrolled_users', courseid=5)

client.list_users()
