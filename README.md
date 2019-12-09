# Rundeck REST API client

This is a Python REST API client for Rundeck 2.6+

Some function or options required are newer Rundeck version and you need to pass
a associated `api_version` to the constructor.

## Example

```python
from pyrundeck import Rundeck

rundeck = Rundeck('http://rundeck-url',
                  token='sometoken',
                  api_version=32,  # this is not mandatory, it defaults to 18
                 )

run = rundeck.run_job(RUNDECK_JOB_ID, options={'option1': 'foo'})

running_jobs = rundeck.get_executions_for_job(job_id=RUNDECK_JOB_ID, status='running')

for job in running_jobs['executions']:
  print("%s is running" % job['id'])
```

A token can be generated in the 'profile' page of Rundeck. Alternatively you
can login with a username and password.


## See also

- https://github.com/marklap/rundeckrun

## LICENSE

GPL3
