# 🚮 Archived!

If you're interested in maintaining this package please get in touch with me at:

https://github.com/pschmitt/contact/issues/new

# Rundeck REST API client

![PyPI](https://img.shields.io/pypi/v/pyrundeck)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyrundeck)
![PyPI - License](https://img.shields.io/pypi/l/pyrundeck)
![Python Lint](https://github.com/pschmitt/pyrundeck/workflows/Python%20Lint/badge.svg)

This is a Python REST API client for Rundeck 2.6+

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

Example using the file upload option

```python
from pyrundeck import rundeck

rd = Rundeck(
        rundeck_url,
        username=username,
        password=password,
        verify=False,
        api_version=19  # Required for file upload option
    )
# Use the file_key returned in the response to reference the file when running a job
# Per documentation at https://docs.rundeck.com/docs/api/rundeck-api.html#upload-a-file-for-a-job-option
response = rd.upload_file(RUNDECK_JOB_ID, OPTION_NAME, FILE_NAME_STRING_OR_IOFILEWRAPPER)
file_key = response['options'][OPTION_NAME]
rd.run_job(RUNDECK_JOB_ID, options={OPTION_NAME: file_key})
```

## See also

- https://github.com/marklap/rundeckrun

## LICENSE

GPL3
