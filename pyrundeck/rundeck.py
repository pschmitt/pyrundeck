#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals
from __future__ import print_function
import logging
import os
import requests

try:
    # Python 2
    from urlparse import urljoin
except ModuleNotFoundError:
    # Python 3
    from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class Rundeck(object):
    def __init__(
        self,
        rundeck_url,
        token=None,
        username=None,
        password=None,
        api_version=18,
        verify=True,
    ):
        self.rundeck_url = rundeck_url
        self.API_URL = urljoin(rundeck_url, "/api/{}".format(api_version))
        self.token = token
        self.username = username
        self.password = password
        self.verify = verify
        self.auth_cookie = None
        if self.token is None:
            self.auth_cookie = self.auth()

    def auth(self):
        url = urljoin(self.rundeck_url, "/j_security_check")
        p = {"j_username": self.username, "j_password": self.password}
        r = requests.post(
            url,
            data=p,
            verify=self.verify,
            # Disable redirects, otherwise we get redirected twice and need to
            # return r.history[0].cookies['JSESSIONID']
            allow_redirects=False,
        )
        return r.cookies["JSESSIONID"]

    def __request(self, method, url, params=None):
        logger.info("{} {} Params: {}".format(method, url, params))
        cookies = dict()
        if self.auth_cookie:
            cookies["JSESSIONID"] = self.auth_cookie

        h = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Rundeck-Auth-Token": self.token,
        }
        options = {
            "cookies": cookies,
            "headers": h,
            "verify": self.verify,
        }
        if method == "GET":
            options["params"] = params
        else:
            options["json"] = params

        r = requests.request(method, url, **options)
        logger.debug(r.content)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            logger.error(e.message)
            return r.content

    def __get(self, url, params=None):
        return self.__request("GET", url, params)

    def __post(self, url, params=None):
        return self.__request("POST", url, params)

    def __delete(self, url, params=None):
        return self.__request("DELETE", url, params)

    def list_tokens(self, user=None):
        url = "{}/tokens".format(self.API_URL)
        if user:
            url += "/{}".format(user)
        return self.__get(url)

    def get_token(self, token_id):
        url = "{}/token/{}".format(self.API_URL, token_id)
        return self.__get(url)

    def create_token(self, user):
        url = "{}/tokens/{}".format(self.API_URL, user)
        return self.__post(url)

    def delete_token(self, token_id):
        url = "{}/token/{}".format(self.API_URL, token_id)
        return self.__delete(url)

    def system_info(self):
        url = "{}/system/info".format(self.API_URL)
        return self.__get(url)

    def set_active_mode(self):
        url = "{}/system/executions/enable".format(self.API_URL)
        return self.__post(url)

    def set_passive_mode(self):
        url = "{}/system/executions/disable".format(self.API_URL)
        return self.__post(url)

    def list_system_acl_policies(self):
        url = "{}/system/acl/".format(self.API_URL)
        return self.__get(url)

    def get_acl_policy(self, policy):
        url = "{}/system/acl/{}".format(self.API_URL, policy)
        return self.__get(url)

    def list_projects(self):
        url = "{}/projects".format(self.API_URL)
        return self.__get(url)

    def list_jobs(self, project):
        url = "{}/project/{}/jobs".format(self.API_URL, project)
        return self.__get(url)

    def list_all_jobs(self):
        jobs = []
        for p in self.list_projects():
            jobs += self.list_jobs(p["name"])
        return jobs

    def get_job(self, name, project=None):
        if project:
            jobs = self.list_jobs(project)
        else:
            jobs = []
            for p in self.list_projects():
                jobs += self.list_jobs(p["name"])
        return next(job for job in jobs if job["name"] == name)

    def get_running_jobs(self, project, job_id=None):
        """This requires API version 32"""
        url = "{}/project/{}/executions/running".format(self.API_URL, project)
        params = None
        if job_id is not None:
            params = {
                "jobIdFilter": job_id,
            }
        return self.__get(url, params=params)

    def run_job(
        self,
        job_id,
        args=None,
        options=None,
        log_level=None,
        as_user=None,
        node_filter=None,
    ):
        url = "{}/job/{}/run".format(self.API_URL, job_id)
        params = {
            "logLevel": log_level,
            "asUser": as_user,
            "filter": node_filter,
        }
        if options is None:
            params["argString"] = args
        else:
            params["options"] = options
        return self.__post(url, params=params)

    def run_job_by_name(self, name, *args, **kwargs):
        job = self.get_job(name)
        return self.run_job(job["id"], *args, **kwargs)

    def get_executions_for_job(self, job_id=None, job_name=None, **kwargs):
        # http://rundeck.org/docs/api/#getting-executions-for-a-job
        if not job_id:
            if not job_name:
                raise RuntimeError("Either job_name or job_id is required")
            job_id = self.get_job(job_name).get("id")
        url = "{}/job/{}/executions".format(self.API_URL, job_id)
        return self.__get(url, params=kwargs)

    def query_executions(
        self,
        project,
        name=None,
        group=None,
        status=None,
        user=None,
        recent=None,
        older=None,
        begin=None,
        end=None,
        adhoc=None,
        max_results=20,
        offset=0,
    ):
        # http://rundeck.org/docs/api/#execution-query
        url = "{}/project/{}/executions".format(self.API_URL, project)
        params = {
            "jobListFilter": name,
            "userFilter": user,
            "groupPath": group,
            "statusFilter": status,
            "adhoc": adhoc,
            "recentFilter": recent,
            "olderFilter": older,
            "begin": begin,
            "end": end,
            "max": max_results,
            "offset": offset,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self.__get(url, params=params)

    def list_running_executions(self, project):
        url = "{}/project/{}/executions/running".format(self.API_URL, project)
        return self.__get(url)

    def execution_state(self, exec_id):
        url = "{}/execution/{}/state".format(self.API_URL, exec_id)
        return self.__get(url)

    def list_jobs_by_group(self, project, groupPath=None):
        url = "{}/project/{}/jobs".format(self.API_URL, project)
        params = {"groupPath": groupPath}
        return self.__post(url, params=params)

    def execution_output_by_id(self, exec_id):
        url = "{}/execution/{}/output".format(self.API_URL, exec_id)
        return self.__get(url)

    def execution_info_by_id(self, exec_id):
        url = "{}/execution/{}".format(self.API_URL, exec_id)
        return self.__get(url)

    def abort_execution(self, exec_id):
        url = "{}/execution/{}/abort".format(self.API_URL, exec_id)
        return self.__get(url)

    def delete_execution(self, exec_id):
        url = "{}/execution/{}".format(self.API_URL, exec_id)
        return self.__delete(url)

    def bulk_delete_executions(self, exec_ids):
        url = "{}/executions/{}/delete".format(self.API_URL)
        params = {"ids": exec_ids}
        return self.__post(url, params=params)

    def list_resources(self, project):
        url = "{}/project/{}/resources".format(self.API_URL, project)
        return self.__get(url)

    def get_resource_info(self, project, resource):
        url = "{}/project/{}/resource/{}".format(
            self.API_URL, project, resource
        )
        return self.__get(url)


if __name__ == "__main__":
    from pprint import pprint

    rundeck_url = os.environ.get("RUNDECK_URL")
    username = os.environ.get("RUNDECK_USER")
    password = os.environ.get("RUNDECK_PASS")
    assert rundeck_url, "Rundeck URL is required"
    assert username, "Username is required"
    assert password, "Password is required"
    rd = Rundeck(
        rundeck_url, username=username, password=password, verify=False
    )
    pprint(rd.list_projects())
    pprint(rd.list_all_jobs())
