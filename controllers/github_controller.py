import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import os
import sys
from github3 import login
from github3.exceptions import UnprocessableResponseBody

BLOCKED_LABEL = 'BLOCKED'

ignore = os.environ.get('IGNORE_WORDS')
IGNORE_WORDS = [i.lower().strip() for i in ignore.split(',')] if ignore else []

ignore_users = os.environ.get('IGNORE_USERS', '').lower()
IGNORE_USERS = [i.strip() for i in ignore_users.split(',')] if ignore_users else []

repositories = os.environ.get('REPOSITORIES').lower()
REPOSITORIES = [r.strip() for r in repositories.split(',')] if repositories else []

REPOSITORY_REGEX = os.environ.get('REPOSITORY_REGEX', None)

user_names = os.environ.get('USER_NAMES')
USER_NAMES = [u.lower().strip() for u in user_names.split(',')] if user_names else []

TIME_EVALUATED = int(os.environ.get('TIME_EVALUATED', 30))

MAX_PR_TO_CHECK = int(os.environ.get('MAX_PR_TO_CHECK', 200))

try:
    GITHUB_API_TOKEN = os.environ['GITHUB_API_TOKEN']
    ORGANIZATION = os.environ['ORGANIZATION']
except KeyError as error:
    sys.stderr.write('Please set the environment variable {0}'.format(error))
    sys.exit(1)


def fetch_organization_repositories():
    """
    Returns a list of repositories for the ORGANIZATION filtered by REPOSITORIES environment Variable.
    """
    pattern = None
    client = login(token=GITHUB_API_TOKEN)
    organization = client.organization(ORGANIZATION)
    if REPOSITORY_REGEX is not None or REPOSITORY_REGEX != '':
        pattern = re.compile(REPOSITORY_REGEX)

    repos = []

    for repository in organization.repositories():
        if ((REPOSITORIES and repository.name.lower() not in REPOSITORIES)
                and not (REPOSITORY_REGEX is not None and REPOSITORY_REGEX != '' and bool(
                    pattern.match(str(repository.name.lower()))))):
            continue
        repos.append(repository)

    return repos


def fetch_open_pulls_requests_formatted(repositories_list):
    """
    Returns a formatted string list of open pull request messages.
    """
    lines = []

    for repository in repositories_list:
        unchecked_pulls = fetch_repository_open_pulls(repository)
        lines += format_pull_requests(unchecked_pulls, ORGANIZATION,
                                      repository.name)

    return lines


def fetch_repository_open_pulls(repository):
    pulls = []

    for pull in repository.pull_requests():
        if pull.state == 'open' and (not USER_NAMES or pull.user.login.lower() in USER_NAMES):
            pulls.append(pull)
    return pulls


def duration(created_at):
    current_date = datetime.now().replace(tzinfo=None)
    return (current_date - created_at.replace(tzinfo=None)).days


def get_review_statuses(pull):
    dict = defaultdict(set)

    for review in pull.reviews():
        if review.state == 'APPROVED':
            state = ':white_check_mark:'
        elif review.state == 'CHANGES_REQUESTED':
            state = ':o:'
        else:
            continue

        dict[state].add('@{0}'.format(review.user.login))

    if dict:
        line = 'Reviews: ' + ' '.join(['{0} by {1}'.format(key, ', '.join(value)) for (key, value) in dict.items()])
    else:
        line = 'No reviews :warning:'

    return line


def format_pull_requests(pull_requests, owner, repository):
    lines = []

    for pull in pull_requests:
        if is_valid_title(pull.title):
            creator = pull.user.login
            review_statuses = get_review_statuses(pull)
            days = duration(pull.created_at)
            text = ' » *[{0}/{1}]* <{2}|{3} - by {4}> - *since {5} day(s)*'.format(
                owner, repository, pull.html_url, pull.title, creator, days, review_statuses)
            lines.append({
                "text": text,
                "is_blocked": as_label(pull, BLOCKED_LABEL),
                "reviews": count_pull_request_reviews(pull)
            })

    return lines


def fetch_repository_all_pulls(repository):
    pulls = []

    for pull in repository.pull_requests(state='all', number=MAX_PR_TO_CHECK):
        if pull.created_at >= (datetime.now(tz=timezone.utc) + timedelta(-TIME_EVALUATED)):
            pulls.append(pull)
    return pulls


def is_valid_title(title):
    lowercase_title = title.lower()
    for ignored_word in IGNORE_WORDS:
        if ignored_word in lowercase_title:
            return False

    return True


def get_last_statistics(weeks, parameter):
    count = 0
    for week in weeks:
        count += week[parameter]
    return count


def fetch_contributor_statistics(repositories_list):
    statistics = {}
    e_tag = None
    last_status = 0
    contributions = None

    for repository in repositories_list:
        contributions = repository.contributor_statistics()

        # for contrib in contributions:
        while True:
            try:
                contrib = next(contributions, None)

                # while contributions.last_status == 202:
                #   print('Waiting After Iterator')

                if contrib is None:
                    break

                if ((len(IGNORE_USERS) == 0 or contrib.author.login.lower() not in IGNORE_USERS)
                        and (len(USER_NAMES) == 0 or contrib.author.login.lower() in USER_NAMES)):
                    c = get_last_statistics(
                        contrib.weeks[len(contrib.weeks) - int(TIME_EVALUATED): len(contrib.weeks)], 'c')
                    a = get_last_statistics(
                        contrib.weeks[len(contrib.weeks) - int(TIME_EVALUATED): len(contrib.weeks)], 'a')
                    d = get_last_statistics(
                        contrib.weeks[len(contrib.weeks) - int(TIME_EVALUATED): len(contrib.weeks)], 'd')

                    if contrib.author.login not in statistics:
                        statistics[contrib.author.login] = {
                            'commits': 0,
                            'additions': 0,
                            'deletions': 0
                        }

                    statistics[contrib.author.login]['commits'] += c
                    statistics[contrib.author.login]['additions'] += a
                    statistics[contrib.author.login]['deletions'] += d
            except UnprocessableResponseBody:
                print('Error 202')
                time.sleep(1)
    return statistics


def as_label(pull, text):
    for label in pull.labels:
        if str(label['name']).upper() == text:
            return True
    return False


def count_pull_request_reviews(pull_request):
    reviews = {}
    author = pull_request.user.login
    pr_reviews = pull_request.reviews()

    for r in pr_reviews:
        if r.user.login != author:
            if r.user.login in reviews:
                if r.state != 'COMMENTED':
                    reviews[r.user.login] = r.state
            else:
                reviews[r.user.login] = r.state

    result = {
        'APPROVED': 0,
        'CHANGES_REQUESTED': 0,
        'PENDING': 0,
        'COMMENTED': 0
    }

    for _, value in reviews.items():
        if value in ['APPROVED', 'CHANGES_REQUESTED', 'PENDING', 'COMMENTED']:
            result[value] = result[value] + 1

    return result


def fetch_user_reviews_count(pull_request):
    reviews = {}

    for p in pull_request:
        for r in p.reviews():
            if not IGNORE_USERS or r.user.login.lower() not in IGNORE_USERS:
                reviews[r.user.login] = {'reviews': reviews[r.user.login]['reviews'] + 1} \
                    if r.user.login in reviews and 'reviews' in reviews[r.user.login] \
                    else {'reviews': 1}

    return reviews


def fetch_users_without_reviews(repositories_list):
    reviews = {}

    for repository in repositories_list:
        users = repository.collaborators()
        for user in users:
            if not IGNORE_USERS or user.login.lower() not in IGNORE_USERS:
                reviews[user.login] = {
                    'reviews': 0
                }

    return reviews


def fetch_organization_raw_pulls(repositories_list):
    """
    Returns a raw list of pull request.
    """
    lines = []

    for repository in repositories_list:
        repos = fetch_repository_all_pulls(repository)
        lines += repos

    return lines


def fetch_users_pr_author(pull_request_list):
    authors = {}
    for pr in pull_request_list:
        if pr.user.login not in authors:
            authors[pr.user.login] = {
                'pr_count': 0
            }
        authors[pr.user.login]['pr_count'] += 1
    return authors
