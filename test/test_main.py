from unittest.mock import Mock, patch

from tasks.main import run_task


# TODO: Test the `main` task itself

@patch('requests.post')
def test_run_task(mock_post):
    mock_ctx = Mock()

    priv_values = ['IM_PRIVATE']
    fake_callback = 'https://logs.example.com'
    flags_dict = {
        'fake-flag': 'flag-val',
        'other-flag': 'other-val',
    }

    env = {
        'ENV_VAR', 'env-val',
    }

    run_task(mock_ctx, 'fake-task', priv_values, fake_callback,
             flags_dict=flags_dict, env=env)

    mock_post.assert_called_once()

    mock_ctx.run.assert_called_once_with(
        'inv fake-task fake-flag=flag-val other-flag=other-val', env=env)
