from unittest.mock import Mock

from tasks.main import run_task


# TODO: Test the `main` task itself

def test_run_task():
    mock_ctx = Mock()

    priv_values = ['IM_PRIVATE']
    flags_dict = {
        'fake-flag': 'flag-val',
        'other-flag': 'other-val',
    }

    env = {
        'ENV_VAR', 'env-val'
    }

    run_task(mock_ctx, 'fake-task', priv_values,
             flags_dict=flags_dict, env=env)

    mock_ctx.run.assert_called_once()

    call_args = mock_ctx.run.call_args

    assert call_args[0] == (
        'inv fake-task fake-flag=flag-val other-flag=other-val',)
    assert call_args[1]['env'] == env
    assert call_args[1]['out_stream']
    assert call_args[1]['err_stream']
