from flask import Flask, request, jsonify
import pika
import os
import pdb
from pymongo import MongoClient
from github import update_github_status


app = Flask(__name__)

# endpoint to create new user
@app.route("/github", methods=["POST"])
def process_pr():
    #print(request.json)
    repo      = request.json['pull_request']['head']['repo']['html_url']
    repo_full = request.json['pull_request']['head']['repo']['full_name']
    commit    = request.json['pull_request']['head']['sha']

    base_repo   = request.json['pull_request']['base']['repo']['html_url']
    base_commit = request.json['pull_request']['base']['sha']

    pr_id  = request.json['pull_request']['id']
    pr_url = request.json['pull_request']['url']

    if request.json['review']['state'] == 'approved':
        store_pr_in_db(pr_id, base_repo, base_commit, repo, commit, repo_full)

        update_github_status(repo_full, commit, "pending", "Queued", "http://35.234.68.57/pull_requests/working_on_it.html")

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='127.0.0.1'))
        channel = connection.channel()

        channel.queue_declare(queue='pull_request', durable=True)

        message = '{};{};{};{};{};{}'.format(pr_id, base_repo, base_commit, repo, commit, repo_full)
        channel.basic_publish(
            exchange='',
            routing_key='pull_request',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        print("-Sent {}".format(message))
        connection.close()

    return jsonify({"status_code" : 200})


def store_pr_in_db(pr_id, repo1, commit1, repo2, commit2, repo_full):
    client = MongoClient('127.0.0.1', 27017)
    db = client['github_ic']
    pr_db = db['pull_requests']

    data = {'pr'          : pr_id,
            'base_repo'   : repo1,
            'base_commit' : commit1,
            'repo'        : repo2,
            'repo_full'   : repo_full,
            'commit'      : commit2,
            commit1       : False,
            commit2       : False,
            "nfiles"      : 2}
    pr_db.insert_one(data)

@app.route("/jobs", methods=["POST"])
def finished_job():
    client = MongoClient('127.0.0.1', 27017)
    db = client['github_ic']
    pr_db = db['pull_requests']

    pr_id  = request.json['pr']
    commit = request.json['commit']
    job    = request.json['job']

    jobs_db = db['pr{}_{}'.format(pr_id, commit)]

    data = {'pr'     : pr_id,
            'commit' : commit,
            "job"    : job}
    jobs_db.insert_one(data)


    # check if production is complete
    pr_data = pr_db.find_one({'pr' : int(pr_id)})
    if jobs_db.count() >= pr_data['nfiles']:
        pr_data[commit] = True
        pr_db.update_one({'_id': pr_data['_id']},
                         {"$set": pr_data}, upsert=False)

    check_production_finished(pr_data)

    return jsonify({"status_code" : 200})


def check_production_finished(pr_data):
    commit1 = pr_data['base_commit']
    commit2 = pr_data['commit'     ]
    pr_id   = int(pr_data['pr'])
    if pr_data[commit1] and pr_data[commit2]:
        # Send new message to next queue
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='127.0.0.1'))
        channel_out = connection.channel()
        channel_out.queue_declare(queue='comparison', durable=True)

        message = '{};{};{}'.format(pr_id, commit1, commit2)
        channel_out.basic_publish(
            exchange='',
            routing_key='comparison',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
