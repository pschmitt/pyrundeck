#!/usr/bin/env python
# coding: utf-8
import logging
import os
import requests
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
        self.API_URL = urljoin(rundeck_url, f"/api/{api_version}")
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

    def __request(self, method, url, params=None, headers={}):
        logger.info(f"{method} {url} Params: {params}")
        cookies = dict()
        if self.auth_cookie:
            cookies["JSESSIONID"] = self.auth_cookie

        h = {
            "Accept": "application/json",
            "X-Rundeck-Auth-Token": self.token,
        }
        # See https://github.com/rundeck/rundeck/issues/1923
        if method in ("POST", "PUT"):
            h["Content-Type"] = "application/json"

        # Allow end-users to override headers (ex. "Accept": "text/plain")
        h.update(headers)

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
            if h["Accept"] == "application/json":
                return r.json()
            else:
                return r.text
        except ValueError as e:
            logger.error(e.message)
            return r.content

    def __get(self, url, params=None, headers={}):
        return self.__request("GET", url, params, headers)

    def __post(self, url, params=None, headers={}):
        return self.__request("POST", url, params, headers)

    def __delete(self, url, params=None, headers={}):
        return self.__request("DELETE", url, params, headers)

    def list_tokens(self, user=None):
        url = f"{self.API_URL}/tokens"
        if user:
            url += f"/{user}"
        return self.__get(url)

    def get_token(self, token_id):
        url = f"{self.API_URL}/token/{token_id}"
        return self.__get(url)

    def create_token(self, user):
        url = f"{self.API_URL}/tokens/{user}"
        return self.__post(url)

    def delete_token(self, token_id):
        url = f"{self.API_URL}/token/{token_id}"
        return self.__delete(url)

    def system_info(self):
        url = f"{self.API_URL}/system/info"
        return self.__get(url)

    def set_active_mode(self):
        url = f"{self.API_URL}/system/executions/enable"
        return self.__post(url)

    def set_passive_mode(self):
        url = f"{self.API_URL}/system/executions/disable"
        return self.__post(url)

    def list_system_acl_policies(self):
        url = f"{self.API_URL}/system/acl/"
        return self.__get(url)

    def get_acl_policy(self, policy):
        url = f"{self.API_URL}/system/acl/{policy}"
        return self.__get(url)

    def list_projects(self):
        url = f"{self.API_URL}/projects"
        return self.__get(url)

    def list_jobs(self, project):
        url = f"{self.API_URL}/project/{project}/jobs"
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
        url = f"{self.API_URL}/project/{project}/executions/running"
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
        url = f"{self.API_URL}/job/{job_id}/run"
        params = {"logLevel": log_level, "asUser": as_user, "filter": node_filter}
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
        url = f"{self.API_URL}/job/{job_id}/executions"
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
        url = f"{self.API_URL}/project/{project}/executions"
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
        url = f"{self.API_URL}/project/{project}/executions/running"
        return self.__get(url)

    def execution_state(self, exec_id):
        url = f"{self.API_URL}/execution/{exec_id}/state"
        return self.__get(url)

    def list_jobs_by_group(self, project, groupPath=None):
        url = f"{self.API_URL}/project/{project}/jobs"
        params = {"groupPath": groupPath}
        return self.__post(url, params=params)

    def execution_output_by_id(self, exec_id, output_format=None):
        url = f"{self.API_URL}/execution/{exec_id}/output"
        params = {}
        headers = {}
        if output_format:
            params["format"] = output_format
            if output_format == "xml":
                headers["Accept"] = "application/xml"
            elif output_format == "json":
                headers["Accept"] = "application/json"
            elif output_format == "text":
                headers["Accept"] = "text/plain"

        return self.__get(url, params=params, headers=headers)

    def execution_info_by_id(self, exec_id):
        url = f"{self.API_URL}/execution/{exec_id}"
        return self.__get(url)

    def abort_execution(self, exec_id):
        url = f"{self.API_URL}/execution/{exec_id}/abort"
        return self.__get(url)

    def delete_execution(self, exec_id):
        url = f"{self.API_URL}/execution/{exec_id}"
        return self.__delete(url)

    def bulk_delete_executions(self, exec_ids):
        url = f"{self.API_URL}/executions/delete"
        params = {"ids": exec_ids}
        return self.__post(url, params=params)


if __name__ == "__main__":
    from pprint import pprint

    rundeck_url_ = os.environ.get("RUNDECK_URL")
    username_ = os.environ.get("RUNDECK_USER")
    password_ = os.environ.get("RUNDECK_PASS")
    assert rundeck_url_, "Rundeck URL is required"
    assert username_, "Username is required"
    assert password_, "Password is required"
    rd = Rundeck(rundeck_url_, username=username_, password=password_, verify=False)
    pprint(rd.list_projects())
    pprint(rd.list_all_jobs())
