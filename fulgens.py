#!/usr/bin/env python3

import json
import os
import pathlib

import click
import gitlab

from getpass import getpass
from typing import Optional, List

from gitlab.v4.objects.projects import Project as GLProject
from gitlab.v4.objects.merge_requests import MergeRequest as GLMergeRequest


CONF_PATH = pathlib.Path().home().joinpath(".config/fulgens")



def set_token() -> None:
    config_file_path = CONF_PATH.joinpath("config.json")
    token = getpass("Your gitlab personal token: ")

    try:
        with open(config_file_path) as inf:
            config = json.load(inf)
    except FileNotFoundError:
        config = {}

    config["gitlab_token"] = token

    # ensure config directory exists
    try:
        CONF_PATH.mkdir(parents=True)
    except FileExistsError:
        pass

    with open(config_file_path, "w") as outf:
        json.dump(config, outf)

    # make sure that the file is read-only for the user
    os.chmod(config_file_path, 0o600)


def get_token() -> Optional[str]:
    config_file_path = CONF_PATH.joinpath("config.json")
    try:
        with open(config_file_path) as inf:
            return json.load(inf)["gitlab_token"]
    except FileNotFoundError:
        return None


def _get_projects(gl: gitlab.Gitlab) -> List[GLProject]:
    projects = []

    for g in gl.groups.list():
        for p in g.projects.list():
            # These projects are GroupProjects and do not contain merge request data
            projects.append(gl.projects.get(p.get_id()))

    return projects


def report_merge_requests(filter: Optional[dict[str, str]]) -> None:
    gl = gitlab.Gitlab("https://gitlab.com", private_token=get_token())
    gl.auth()

    for p in _get_projects(gl):
        merge_requests = p.mergerequests.list(**filter)

        if len(merge_requests) > 0:
            print(f"{p.name}")
            for mr in merge_requests:
                #if gl.user.id not in [r["id"] for r in mr.reviewers]:
                #    continue

                desc = mr.description + " " if len(mr.description) > 0 else ""
                print(f"  MR#{mr.iid} ({mr.state}) {desc}({mr.attributes['web_url']})")


@click.command()
@click.option(
    "--include-closed", help="Include closed merge requests in filters", is_flag=True
)
@click.argument("command", required=True)
def main(include_closed: bool, command: str) -> None:
    if command == "set-token":
        set_token()
    elif command == "report-mrs":
        mr_filter = {"state": "opened"}

        if include_closed:
            mr_filter = {}

        report_merge_requests(mr_filter)


if __name__ == "__main__":
    main()
