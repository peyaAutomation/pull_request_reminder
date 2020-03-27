import os
import controllers.slack_post_controller as slack
import controllers.github_controller as github

MIN_OF_REVIEW = int(os.environ.get('MIN_OF_REVIEW', 0))
ORDER_CRITERIA = os.environ.get('ORDER_CRITERIA', "Top")
RANKING_QTY = int(os.environ.get('RANKING_QTY', 5))


def pull_request_reminder():
    repositories = github.fetch_organization_repositories()
    pull_requests = github.fetch_open_pulls_requests_formatted(repositories)

    blockeds = []
    ready_to_merge = []
    waiting_for_approvals = []
    changes_needed = []

    for pr in pull_requests:
        if pr['is_blocked']:
            blockeds.append(pr)
        else:
            if pr['reviews']['CHANGES_REQUESTED'] > 0 or pr['reviews']['COMMENTED'] > 0:
                changes_needed.append(pr)
            elif pr['reviews']['APPROVED'] >= MIN_OF_REVIEW:
                ready_to_merge.append(pr)
            else:
                waiting_for_approvals.append(pr)

    slack.post_pull_reminder(ready_to_merge, waiting_for_approvals, changes_needed, blockeds)


def top_bottom_reviewers():
    repositories_list = github.fetch_organization_repositories()
    pull_requests = github.fetch_organization_raw_pulls(repositories_list)
    all_users = github.fetch_users_without_reviews(repositories_list)
    users_with_reviews = github.fetch_user_reviews_count(pull_requests)

    all_users.update(users_with_reviews)
    cv_count = 0

    for item in all_users.items():
        cv_count += item[1]['reviews']

    all_users = sorted(all_users.items(),
                       key=lambda user: user[1]['reviews'],
                       reverse=ORDER_CRITERIA.lower() == 'top')[:RANKING_QTY]

    slack.post_ranking_reviewers(users=all_users, repositories=repositories_list, order=ORDER_CRITERIA,
                                 ranking_qty=RANKING_QTY, cv_count=cv_count, pr_count=len(pull_requests))


def top_bottom_contributions():
    repositories_list = github.fetch_organization_repositories()
    contributor_statistics = github.fetch_contributor_statistics(repositories_list)

    cm_count = 0

    for item in contributor_statistics.items():
        cm_count += item[1]['commits']

    contributor_statistics = sorted(contributor_statistics.items(),
                                    key=lambda user: user[1]['commits'],
                                    reverse=ORDER_CRITERIA.lower() == 'top')[:RANKING_QTY]

    slack.post_ranking_contributions(contributions=contributor_statistics, order=ORDER_CRITERIA,
                                     ranking_qty=RANKING_QTY, cm_count=cm_count)


def top_bottom_pr_authors():
    repositories_list = github.fetch_organization_repositories()
    pull_requests = github.fetch_organization_raw_pulls(repositories_list)
    users = github.fetch_users_pr_author(pull_requests)

    pr_count = len(pull_requests)

    print(pr_count)

    users = sorted(users.items(),
                   key=lambda user: user[1]['pr_count'],
                   reverse=ORDER_CRITERIA.lower() == 'top')[:RANKING_QTY]

    slack.post_ranking_pr_authors(users=users, order=ORDER_CRITERIA,
                                  ranking_qty=RANKING_QTY, pr_count=pr_count)


if __name__ == '__main__':
    pull_request_reminder()
