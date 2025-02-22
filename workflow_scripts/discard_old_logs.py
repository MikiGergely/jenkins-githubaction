import os
from api4jenkins import Jenkins
from github import Github
import logging
import json
import requests
import re
from time import time, sleep

log_level = os.environ.get('INPUT_LOG_LEVEL', 'INFO')
logging.basicConfig(format='JENKINS_ACTION: %(message)s', level=log_level)

def main():
    # Required
    url = os.environ["INPUT_URL"]

    # Optional
    username = os.environ.get("INPUT_USERNAME")
    api_token = os.environ.get("INPUT_API_TOKEN")
    cookies = os.environ.get("INPUT_COOKIES")
    access_token = os.environ.get("INPUT_ACCESS_TOKEN")
    if not access_token:
        raise Exception("Access token is required to connect to github")

    # Predefined

    if username and api_token:
        auth = (username, api_token)
    else:
        auth = None
        logging.info('Username or token not provided. Connecting without authentication.')


    if cookies:
        try:
            cookies = json.loads(cookies)
        except json.JSONDecodeError as e:
            raise Exception('`cookies` is not valid JSON.') from e
    else:
        cookies = {}

    jenkins = Jenkins(url, auth=auth, cookies=cookies)

    try:
        jenkins.version
    except Exception as e:
        raise Exception('Could not connect to Jenkins.') from e

    logging.info('Successfully connected to Jenkins.')
    log_keep_meta={
        "keepLogs" : []
    }
    for log in find_old_logs():
        logging.debug(log)
        build = jenkins.get_job(log["fullName"]).get_build(log["number"])
        keep_logs(build, auth, False)
        log_keep_meta["keepLogs"].append({"build": {"fullName": log["fullName"], "number": log["number"]}, "enabled": False})
    issue_comment("<!--{lkm}-->\n_Discarded old logs_".format(lkm=json.dumps(log_keep_meta)))




def find_old_logs():
    #Comment example: '<!-- {"keepLogs":[{"build": {"fullName": "utils/test", "number": 5}, "enabled": true }]} -->'
    old_logs=set()

    github = Github(os.environ.get("INPUT_ACCESS_TOKEN"))

    github_event_file = open(os.environ.get("GITHUB_EVENT_PATH"), "r")
    github_event = json.loads(github_event_file.read())
    github_event_file.close

    pr_repo_name = github_event["pull_request"]["base"]["repo"]["full_name"]
    pr_number = github_event["number"]
    comments = github.get_repo(pr_repo_name).get_pull(pr_number).as_issue().get_comments()

    logging.info("searching for old logs")
    i=comments.totalCount
    logging.info(f"Found {i} comments")
    j=0
    while i > 0:
        for comment in comments.get_page(j):
            i-=1
            for data in re.findall('<!--(.*)-->', comment.body):
                try:
                    json_data = json.loads(data)
                except json.decoder.JSONDecodeError as e:
                    logging.debug(f"{data}\nNot valid json:\n{e} ")
                else:
                    if "keepLogs" in json_data.keys():
                        for log_data in json_data['keepLogs']:
                            if log_data["enabled"]:
                                old_logs.add(log_data["build"])
                                logging.info("adding {b} to list".format(b=log_data["build"]))
                            else:
                                old_logs.discard(log_data["build"])
                                logging.info("removing {b} from list".format(b=log_data["build"]))
        j+=1
    return old_logs



def keep_logs(build, auth, enabled=True):
    if build.api_json()['keepLog'] == enabled:
        return
    response = requests.post(url=build.url+"toggleLogKeep", auth=auth)
    if not response.ok:
        raise Exception(f"Post request returned {response.status_code}")

def wait_for_build(build,timeout,interval):
    build_url=build.url
    t0 = time()
    sleep(interval)
    while time() - t0 < timeout:
        result = build.result
        if result == 'SUCCESS':
            logging.info(f'Build successful')
            return result
        if result == 'UNSTABLE':
            logging.info(f'Build unstable')
            return result
        if result in ('FAILURE', 'ABORTED'):
            logging.info(f'Build status returned "{result}". Build has failed ☹️.')
            return result
        logging.info(f'Build not finished yet. Waiting {interval} seconds. {build_url}')
        sleep(interval)
    logging.info(f"Build has not finished and timed out. Waited for {timeout} seconds.")
    return "TIMEOUT"


def issue_comment(body):
    g = Github(os.environ.get("INPUT_ACCESS_TOKEN"))

    github_event_file = open(os.environ.get("GITHUB_EVENT_PATH"), "r")
    github_event = json.loads(github_event_file.read())
    github_event_file.close

    pr_repo_name = github_event["pull_request"]["base"]["repo"]["full_name"]
    pr_number = github_event["number"]

    g.get_repo(pr_repo_name).get_pull(pr_number).create_issue_comment(body)


if __name__ == "__main__":
    main()
