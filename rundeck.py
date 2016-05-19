#!/usr/bin/env python
# coding: utf-8


from __future__ import unicode_literals
from __future__ import print_function
import logging
import os
import requests

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Rundeck():
    def __init__(self, rundeck_url, token=None, username=None, password=None,
                 api_version=17, verify=True):
        self.rundeck_url = rundeck_url
        self.API_URL = '{}/api/{}'.format(rundeck_url, api_version)
        self.token = token
        self.username = username
        self.password = password
        self.verify = verify
        self.auth_cookie = self.auth()

    def auth(self):
        url = '{}/j_security_check'.format(self.rundeck_url)
        p = {'j_username': self.username, 'j_password': self.password}
        # Disable redirects, otherwise we get redirected twice and need to
        # return r.history[0].cookies['JSESSIONID']
        r = requests.post(url, params=p, verify=self.verify, allow_redirects=False)
        return r.cookies['JSESSIONID']

    def __request(self, method, url, params=None):
        logger.info('{} {} Params: {}'.format(method, url, params))
        cookies = {'JSESSIONID': self.auth_cookie}
        h = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Rundeck-Auth-Toke': self.token
        }
        r = requests.request(
            method, url, cookies=cookies, headers=h, json=params,
            verify=self.verify
        )
        logger.debug(r.content)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            logger.error(e.message)
            return r.content

    def __get(self, url, params=None):
        return self.__request('GET', url, params)

    def __post(self, url, params=None):
        return self.__request('POST', url, params)

    def __delete(self, url, params=None):
        return self.__request('DELETE', url, params)

    def list_tokens(self, user=None):
        url = '{}/tokens'.format(self.API_URL)
        if user:
            url += '/{}'.format(user)
        return self.__get(url)

    def get_token(self, token_id):
        url = '{}/token/{}'.format(self.API_URL, token_id)
        return self.__get(url)

    def create_token(self, user):
        url = '{}/tokens/{}'.format(self.API_URL, user)
        return self.__post(url)

    def delete_token(self, token_id):
        url = '{}/token/{}'.format(self.API_URL, token_id)
        return self.__delete(url)

    def system_info(self):
        url = '{}/system/info'.format(self.API_URL)
        return self.__get(url)

    def set_active_mode(self):
        url = '{}/system/executions/enable'.format(self.API_URL)
        return self.__post(url)

    def set_passive_mode(self):
        url = '{}/system/executions/disable'.format(self.API_URL)
        return self.__post(url)

    def list_system_acl_policies(self):
        url = '{}/system/acl/'.format(self.API_URL)
        return self.__get(url)

    def get_acl_policy(self, policy):
        url = '{}/system/acl/{}'.format(self.API_URL, policy)
        return self.__get(url)

    def list_projects(self):
        url = '{}/projects'.format(self.API_URL)
        return self.__get(url)

    def list_jobs(self, project):
        url = '{}/project/{}/jobs'.format(self.API_URL, project)
        return self.__get(url)

    def list_all_jobs(self):
        jobs = []
        for p in self.list_projects():
            jobs += self.list_jobs(p['name'])
        return jobs

    def get_job(self, name, project=None):
        if project:
            jobs = self.list_jobs(project)
        else:
            jobs = []
            for p in self.list_projects():
                jobs += self.list_jobs(p['name'])
        return next(job for job in jobs if job['name'] == name)

    def run_job(self, job_id, args=None, log_level=None, as_user=None,
                node_filter=None):
        url = '{}/job/{}/run'.format(self.API_URL, job_id)
        params = {
            'argString': args,
            'logLevel': log_level,
            'asUser': as_user,
            'filter': node_filter
        }
        return self.__post(url, params=params)

    def run_job_by_name(self, name, args=None, log_level=None, as_user=None,
                        node_filter=None):
        job = self.get_job(name)
        return self.run_job(job['id'], args, log_level, as_user, node_filter)

    def list_running_executions(self, project):
        url = '{}/project/{}/executions/running'.format(self.API_URL, project)
        return self.__get(url)


if __name__ == '__main__':
    from pprint import pprint
    rundeck_url = os.environ.get('RUNDECK_URL')
    username = os.environ.get('RUNDECK_USER')
    password = os.environ.get('RUNDECK_PASS')
    assert rundeck_url, 'Rundeck URL is required'
    assert username, 'Username is required'
    assert password, 'Password is required'
    rd = Rundeck(
        rundeck_url, username=username, password=password,
        verify=False
    )
    pprint(rd.list_projects())
    pprint(rd.list_all_jobs())
