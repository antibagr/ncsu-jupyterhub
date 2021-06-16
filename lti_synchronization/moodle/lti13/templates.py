def get_lti13_keys(target_link_url) -> dict:
    return {
    'title': 'NCSU',
    'scopes': [
        'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem',
        'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly',
        'https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly',
        'https://purl.imsglobal.org/spec/lti-ags/scope/score',
        'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly',
        'https://moodle.instructure.com/lti/public_jwk/scope/update',
        'https://moodle.instructure.com/lti/data_services/scope/create',
        'https://moodle.instructure.com/lti/data_services/scope/show',
        'https://moodle.instructure.com/lti/data_services/scope/update',
        'https://moodle.instructure.com/lti/data_services/scope/list',
        'https://moodle.instructure.com/lti/data_services/scope/destroy',
        'https://moodle.instructure.com/lti/data_services/scope/list_event_types',
        'https://moodle.instructure.com/lti/feature_flags/scope/show',
        'https://moodle.instructure.com/lti/account_lookup/scope/show',
    ],
    'extensions': [
        {
            'platform': 'moodle.instructure.com',
            'settings': {
                'platform': 'moodle.instructure.com',
                'placements': [
                    {
                        'placement': 'course_navigation',
                        'message_type': 'LtiResourceLinkRequest',
                        'windowTarget': '_blank',
                        'target_link_uri': target_link_url,
                        'custom_fields': {
                            'email': '$Person.email.primary',
                            'lms_user_id': '$User.id',
                        },  # noqa: E231
                    },
                    {
                        'placement': 'assignment_selection',
                        'message_type': 'LtiResourceLinkRequest',
                        'target_link_uri': target_link_url,
                    },
                ],
            },
            'privacy_level': 'public',
        }
    ],
    'description': 'NCSU Learning Tools Interoperability (LTI) v1.3 tool.',
    'custom_fields': {
        'email': '$Person.email.primary',
        'lms_user_id': '$User.id',
    },  # noqa: E231
    'public_jwk_url': f'{target_link_url}hub/lti13/jwks',
    'target_link_uri': target_link_url,
    'oidc_initiation_url': f'{target_link_url}hub/oauth_login',
}
