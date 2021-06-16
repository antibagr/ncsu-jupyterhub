from unittest.mock import patch
from moodle.integration.manager import SyncManager


def test_manager_keyword_arguments():
    '''
    It's important for manager to divirse update_jupyterhub method's arguments
    from filters.
    '''

    manager = SyncManager()

    with patch.object(manager, 'process_data') as mock_process:
        with patch.object(manager, 'temp') as temp:

            manager.update_jupyterhub(
                course_id=('foo', 'bar'),
                title='Foo Bar',
                json_path='json',
                id=1,
            )

            mock_process.assert_called_once_with(
                None, 'json', course_id=('foo', 'bar'), title='Foo Bar', id=1)

            # should suppress KeyboardInterrupt
            temp.get_default.side_effect = KeyboardInterrupt

            manager.update_jupyterhub()
