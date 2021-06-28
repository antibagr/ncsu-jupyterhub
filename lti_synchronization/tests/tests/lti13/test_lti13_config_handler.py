import json
from unittest.mock import MagicMock, patch

import pytest
from moodle.lti13.handlers import LTI13ConfigHandler
from tornado.web import RequestHandler


def test_get_method_calls_write_method(mock_write: MagicMock):
    '''
    Is the write method used in get method?
    '''

    assert mock_write.called


def test_get_calls_write_method_with_a_json(mock_write: MagicMock):
    '''
    Does the write base method is invoked with a string?
    '''

    # call_args is a list
    write_args = mock_write.call_args[0]

    # write_args == tuple
    json_arg = write_args[0]

    assert type(json_arg) == str

    assert json.loads(json_arg)


def test_get_method_writes_a_json_with_required_keys(json_arg: dict):
    '''
    Does the get method write a json (jwks) with essential fields?
    '''

    keys_at_0_level_expected: set = {
        'title',
        'target_link_uri',
        'scopes',
        'public_jwk_url',
        # 'public_jwk',
        'oidc_initiation_url',
        'extensions',
        'custom_fields',
    }

    for key in keys_at_0_level_expected:
        assert key in json_arg


def test_get_method_writes_our_company_name_in_the_title_field(json_arg: dict):
    '''
    Does the get method write 'NCSU' value as the title in the json?
    '''

    assert json_arg.get('title') == 'NCSU'


def test_get_method_writes_email_field_within_custom_fields(json_arg: dict):
    '''
    Does the get method write 'email' field as a custom_fields?
    '''

    custom_fields = json_arg['custom_fields']

    assert 'email' in custom_fields
    assert custom_fields['email'] == '$Person.email.primary'


@pytest.mark.parametrize('field,value', [
    ('lms_user_id', '$User.id'),
    ('email', '$Person.email.primary'),
])
def test_abc(json_arg: dict, field: str, value: str):
    '''
    test_get_method_writes_lms_user_id_custom_field_within_each_course_nav_placement

    Does the get method write 'lms_user_id' field in custom_fields
    within each course_navigation placement setting?

    Does the get method write 'email' field in
    custom_fields within each course_navigation placement setting?
    '''

    extensions = json_arg['extensions']

    # course navigation placement
    course_nav_placement = None

    for ext in extensions:

        # find the settings field in each extension
        # to ensure a course_navigation placement was used
        if 'settings' in ext and 'placements' in ext['settings']:
            course_nav_placement = [
                placement
                for placement in ext['settings']['placements']
                if placement['placement'] == 'course_navigation'
            ]

            assert course_nav_placement

            placement_custom_fields = course_nav_placement[0]['custom_fields']

            assert placement_custom_fields
            assert placement_custom_fields['lms_user_id']
            assert placement_custom_fields['lms_user_id'] == '$User.id'


def test_get_method_writes_lms_user_id_field_within_custom_fields(json_arg: dict):
    '''
    Does the get method write 'lms_user_id' field
    within custom_fields and use the $User.id property?
    '''

    custom_fields = json_arg['custom_fields']

    assert 'lms_user_id' in custom_fields

    assert custom_fields['lms_user_id'] == '$User.id'
