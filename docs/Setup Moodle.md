# Create REST API service

Follow steps described in the link below to create REST API service:

https://<your_moodle_domain>.com/admin/category.php?category=webservicesettings

Enable REST protocol, create specific user to access your moodle API.
Login as this user and agree with Moodle Policy.
Create external service (for instance, rest_api_service).
Add functions to the new service going by
Site administration / Plugins / Web services / External services / Functions

(up-to-date list of functions is available via MoodleClient.functions attribute)

- core_course_get_courses
- core_enrol_get_enrolled_users

Create a token for REST API user. Paste it to .env file as follow:
MOODLE_REST_API_TOKEN=<generated_token>

Check that Moodle is published as LTI Tool

https://docs.moodle.org/311/en/Publish_as_LTI_tool
