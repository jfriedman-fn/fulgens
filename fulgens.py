#!/usr/bin/env python3

import json
import os
import pathlib

import click
import gitlab

from getpass import getpass
from typing import Optional, List

from gitlab.v4.objects.projects import Project as GLProject
from gitlab.v4.objects.groups import Group as GLGroup
from gitlab.v4.objects.merge_requests import MergeRequest as GLMergeRequest


CONF_PATH = pathlib.Path().home().joinpath(".config/fulgens")
GITLAB_TOKEN = None


class Fulgens(object):
    def __init__(self, gitlab_token, gitlab_url="https://gitlab.com"):
        self.gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
        self.gl.auth()

        self.clear_cached_data()

    @classmethod
    def from_config(cls, config: dict[str, any]):
        if "gitlab_token" not in config:
            raise Exception("GitLab token must be provided")

        if "gitlab_url" not in config:
            config["gitlab_url"] = "https://gitlab.com"

        return cls(**config)

    def get_groups(self) -> List[GLGroup]:
        if len(self.groups) == 0:
            for group in self.gl.groups.list():
                self.groups.append(group)

        return self.groups

    def get_projects(self) -> List[GLProject]:
        if len(self.projects) == 0:
            for g in self.get_groups():
                for p in g.projects.list():
                    # These projects are GroupProjects and do not contain merge request data
                    self.projects.append(self.gl.projects.get(p.get_id()))

        return self.projects

    def get_merge_requests(self, **kwargs):
        if len(self.merge_requests) == 0:
            for project in self.get_projects():
                for mr in project.mergerequests.list(**kwargs):
                    self.merge_requests.append(mr)

        return self.merge_requests

    def get_merge_requests_by_project(self, **kwargs):
        mr_by_proj = {}

        for mr in self.get_merge_requests(**kwargs):
            if mr.project_id not in mr_by_proj:
                mr_by_proj[mr.project_id] = []

            mr_by_proj[mr.project_id].append(mr)

        return mr_by_proj

    def get_project(self, project_id):
        try:
            return self._get_projects_by_id()[project_id]
        except IndexError:
            return None

    def clear_cached_data(self):
        self.groups = []
        self.projects = []
        self.merge_requests = []
        self._projects_by_id = {}

    def _get_projects_by_id(self):
        if len(self._projects_by_id) == 0:
            for p in self.projects:
                self._projects_by_id[p.id] = p

        return self._projects_by_id


def get_config() -> dict[str, any]:
    config_file_path = CONF_PATH.joinpath("config.json")
    try:
        with open(config_file_path) as inf:
            config = json.load(inf)
    except FileNotFoundError:
        config = {"gitlab_url": "https://gitlab.com"}

    return config


def save_config(config: dict[str, any]):
    config_file_path = CONF_PATH.joinpath("config.json")

    # ensure config directory exists
    try:
        CONF_PATH.mkdir(parents=True)
    except FileExistsError:
        pass

    with open(config_file_path, "w") as outf:
        json.dump(config, outf)

    # make sure that the file is read-only for the user
    os.chmod(config_file_path, 0o600)


def report_merge_requests(fulgens: Fulgens, filter: Optional[dict[str, str]]) -> None:
    merge_requests = fulgens.get_merge_requests_by_project(**filter)

    if len(merge_requests) > 0:
        for proj_id, mrs in merge_requests.items():
            # print(proj_id)
            print(f"{fulgens.get_project(proj_id).name}")
            for mr in mrs:
                desc = mr.description + " " if len(mr.description) > 0 else ""
                print(f"  MR#{mr.iid} ({mr.state}) {desc}({mr.attributes['web_url']})")

            # if gl.user.id not in [r["id"] for r in mr.reviewers]:
            #    continue

            # desc = mr.description + " " if len(mr.description) > 0 else ""


@click.command()
@click.option(
    "--include-closed", help="Include closed merge requests in filters", is_flag=True
)
@click.option("-t", "--token", type=str, help="GitLab private token")
@click.option("-u", "--url", type=str, help="GitLab instance url")
@click.option(
    "-s", "--save-configuration", help="Save provided config data", is_flag=True
)
@click.argument("command", required=True)
def main(
    include_closed: bool,
    token: Optional[str],
    url: str,
    save_configuration: bool,
    command: str,
) -> None:
    config = get_config()
    if token is not None:
        config["gitlab_token"] = token

    if url is not None:
        config["gitlab_url"] = url

    if save_config:
        save_config(config)

    if "gitlab_token" not in config:
        config["gitlab_token"] = getpass("Please enter GitLab private token:")

    if command == "report-mrs":
        fulgens = Fulgens.from_config(config)
        mr_filter = {"state": "opened"}

        if include_closed:
            mr_filter = {}

        report_merge_requests(fulgens, mr_filter)


if __name__ == "__main__":
    main()
