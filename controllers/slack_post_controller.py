import os
import sys
import json
import requests

POST_URL = 'https://slack.com/api/chat.postMessage'
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', 'developatheneabot')

try:
    SLACK_API_TOKEN = os.environ['SLACK_API_TOKEN']
except KeyError as error:
    sys.stderr.write('Please set the environment variable {0}'.format(error))
    sys.exit(1)


def send_to_slack(blocks):

    payload = {
        'token': SLACK_API_TOKEN,
        'channel': SLACK_CHANNEL,
        'as_user': False,
        'blocks': json.dumps(blocks)
    }

    response = requests.post(POST_URL, data=payload)
    answer = response.json()
    if not answer['ok']:
        print(answer)
        raise Exception(answer['error'])


def post_pull_reminder(ready_to_merge=[], waiting_for_approvals=[], changes_needed=[], blocked=[]):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚧 *Open Pull Requests Waiting for Merge* 🚧"
            }
        }
    ]

    if len(ready_to_merge) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for pr in ready_to_merge:
            lines += '\n' + pr['text']

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Ready to Merge:*" + lines
            }
        })

    if len(waiting_for_approvals) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for pr in waiting_for_approvals:
            lines += '\n' + pr['text']

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Waiting for approvals:*" + lines
            }
        })

    if len(changes_needed) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for pr in changes_needed:
            lines += '\n' + pr['text']

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Changes Needed:*" + lines
            }
        })

    if len(blocked) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for pr in blocked:
            lines += '\n' + pr['text']

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Blockeds:*" + lines
            }
        })

    if len(blocked) > 0 or len(ready_to_merge) > 0 or len(waiting_for_approvals) > 0 or len(changes_needed) > 0:
        send_to_slack(blocks)


def post_ranking_reviewers(users=None, repositories=None, order='top', ranking_qty=0, cv_count=0, pr_count=0):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚧 *" + order.capitalize() + " " + (str(ranking_qty) if ranking_qty < len(users) else str(len(users))) + " - Ranking of Reviewers* 🚧"
            }
        }
    ]

    if len(users) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for user_tuple in users:
            lines += '\n' + '» ' + (':crown: ' if users.index(user_tuple) == 0 else '') + user_tuple[0] + ' (' + str(user_tuple[1]['reviews']) + ' reviews)'

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*GitHub User - (Reviews):*" + lines
            }
        })

    if pr_count > 0 and cv_count > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        lines += '\n' + '» Total Pull Request Evaluated: ' + str(pr_count)
        lines += '\n' + '» Total Reviews performed: ' + str(cv_count)

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Statistics:*" + lines
            }
        })

    """
    if len(repositories) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for repository in repositories:
            lines += '\n' + '» ' + repository.name

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Repositories:*" + lines
            }
        })
    """
    if len(users) > 0:
        send_to_slack(blocks)


def post_ranking_contributions(contributions=None, order='top', ranking_qty=0, cm_count=0):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":female-technologist: *" + order.capitalize() + " " + (str(ranking_qty) if ranking_qty < len(contributions) else str(len(contributions))) + " - Commits Count* :male-technologist:"
            }
        }
    ]

    if len(contributions) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for contrib in contributions:
            lines += ('\n' + '» ' + (':crown: ' if contributions.index(contrib) == 0 else '') + contrib[0]
                      + ' ( ' + str(contrib[1]['commits']) + ' commits: `+' + str(contrib[1]['additions']) + '`  `-' + str(contrib[1]['deletions']) + '` )')

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*GitHub User - (Contributions):*" + lines
            }
        })

    if cm_count > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        lines += '\n' + '» Total Commits: ' + str(cm_count)

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Statistics:*" + lines
            }
        })

    if len(contributions) > 0:
        send_to_slack(blocks)


def post_ranking_pr_authors(users=None, order='top', ranking_qty=0, pr_count=0):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":female-technologist: *" + order.capitalize() + " " + (str(ranking_qty) if ranking_qty < len(users) else str(len(users))) + " - Pull Request Authors* :male-technologist:"
            }
        }
    ]

    if len(users) > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        for user in users:
            lines += ('\n' + '» ' + (':crown: ' if users.index(user) == 0 else '') + user[0]
                      + '    `' + str(user[1]['pr_count']) + ' pull requests`')

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*GitHub User - (Pull Requests):*" + lines
            }
        })

    if pr_count > 0:
        blocks.append({
            "type": "divider"
        })

        lines = ''

        lines += '\n' + '» Total Pull Requests: ' + str(pr_count)

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Statistics:*" + lines
            }
        })

    if len(users) > 0:
        send_to_slack(blocks)
