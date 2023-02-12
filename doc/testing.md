
(smadata_venv) C:\workspace\python-smadata2\smadata2>nosetests test_config.py
..............F....
======================================================================
FAIL: smadata2.test_config.TestConfigUTCSystem.test_timezone
----------------------------------------------------------------------
Traceback (most recent call last):
  File "c:\users\frigaarda\envs\smadata_venv\lib\site-packages\nose\case.py", line 198, in runTest
    self.test(*self.arg)
  File "C:\workspace\python-smadata2\smadata2\test_config.py", line 166, in test_timezone
    assert_equals(dt.tzname(), "UTC")
AssertionError: 'Coordinated Universal Time' != 'UTC'
- Coordinated Universal Time
+ UTC


----------------------------------------------------------------------
Ran 19 tests in 0.072s

FAILED (failures=1)

(smadata_venv) C:\workspace\python-smadata2\smadata2>nosetests sma2mon.py

----------------------------------------------------------------------
Ran 0 tests in 0.000s

OK

(smadata_venv) C:\workspace\python-smadata2\smadata2>nosetests test_sma2mon.py
.
----------------------------------------------------------------------
Ran 1 test in 0.008s

OK

(smadata_venv) C:\workspace\python-smadata2\smadata2>nosetests test_datetimeutil.py
......
----------------------------------------------------------------------
Ran 6 tests in 0.743s

OK