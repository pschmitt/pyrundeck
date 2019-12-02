# Rundeck REST API client

This is a Python REST API client for Rundeck 2.6+

The current version needs Rundeck 3.1+ but many parts still work
with older versions of Rundeck if you specify a lower `api_version` argument.

## Example

```python
from pyrundeck import Rundeck

rundeck = Rundeck('http://rundeck-url',
                  token='sometoken',
                  api_version=30,  # this is not mandatory
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
