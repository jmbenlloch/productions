#!/usr/bin/env python
import pika
import time
from subprocess import call
from glob import glob
from os import path
import os
import requests
from pymongo import MongoClient
import pdb

from github import update_github_status

# RabbitMQ connection
connection = pika.BlockingConnection(
  pika.ConnectionParameters(host='127.0.0.1'))
channel = connection.channel()

channel.queue_declare(queue='finished', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


def update_github(pr_id, success, report_fname):
    client = MongoClient('127.0.0.1', 27017)
    db = client['github_ic']
    pr_db = db['pull_requests']

    pr_data   = pr_db.find_one({'pr' : int(pr_id)})

    repo_full = pr_data['repo_full']
    commit    = pr_data['commit']

    rel_path = '/'.join(report_fname.split('/')[4:])
    target_url = 'http://35.234.68.57/{}'.format(rel_path)

    state = "success" if success else "failure"
    description = "Test production worked!" if success else "Test production failed"
    update_github_status(repo_full, commit, state, description, target_url)


def callback(ch, method, properties, body):
    print(" [x] Received {}".format(body))
    pr_id, success, report_fname = body.decode().split(';')

    update_github(pr_id, success, report_fname)

    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='finished', on_message_callback=callback)

channel.start_consuming()
