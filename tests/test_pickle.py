import os
import sys
from typing import Any, Callable, Dict, Optional

from immutabledict import immutabledict

# {{{ test infrastructure


def run_test_with_new_python_invocation(
    f: Callable[..., Any], *args: Any, extra_env_vars: Optional[Dict[str, Any]] = None
) -> None:
    if extra_env_vars is None:
        extra_env_vars = {}

    from base64 import b64encode
    from pickle import dumps
    from subprocess import check_call

    env_vars = {
        "INVOCATION_INFO": b64encode(dumps((f, args))).decode(),
    }
    env_vars.update(extra_env_vars)

    my_env = os.environ.copy()
    my_env.update(env_vars)

    check_call([sys.executable, __file__], env=my_env)


def run_test_with_new_python_invocation_inner() -> None:
    from base64 import b64decode
    from pickle import loads

    f, args = loads(b64decode(os.environ["INVOCATION_INFO"].encode()))

    f(*args)


# }}}


# {{{ test that pickling an immutabledict recomputes the hash on unpickling

_dict_data = {"a": "1", "b": "2", "c": "3"}


def test_pickle_hash() -> None:
    from pickle import dumps

    dict1 = immutabledict(_dict_data)

    # Force creating a cached hash value
    print(hash(dict1))
    assert dict1._hash

    run_test_with_new_python_invocation(
        _test_pickle_hash_stage2, dumps(dict1), hash(dict1)
    )


def _test_pickle_hash_stage2(pickle_dumps: bytes, old_hash: int) -> None:
    from pickle import loads

    # same immutabledict as in test_pickle_hash()
    dict1 = immutabledict(_dict_data)

    dict2 = loads(pickle_dumps)
    assert dict1 == dict2
    print(hash(dict1), hash(dict2), old_hash)

    # If the hash value is restored from the pickle file, then the hash values
    # would not be equal, because the hash changes on each Python execution.
    assert hash(dict1) == hash(dict2)

    # Make sure the hash value has changed after unpickling.
    assert hash(dict2) != old_hash


# }}}


if __name__ == "__main__":
    if "INVOCATION_INFO" in os.environ:
        run_test_with_new_python_invocation_inner()
    elif len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main

        main([__file__])
