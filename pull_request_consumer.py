#!/usr/bin/env python
import pika
import time
from subprocess import call
from github import update_github_status

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='127.0.0.1'))
channel = connection.channel()

channel.queue_declare(queue='pull_request', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] Received {}".format(body))
    pr_id, base_repo, base_commit, repo, commit, repo_full = body.decode().split(';')
    print(base_repo, base_commit, repo, commit)

    update_github_status(repo_full, commit, "pending", "Building images", "http://35.234.68.57/pull_requests/working_on_it.html")

    cmd = "/home/jmbenlloch/server/docker_build.sh {} {}".format(repo, commit)
    print(cmd)
    fail = call(cmd, shell=True, executable='/bin/bash')

    cmd = "/home/jmbenlloch/server/docker_build.sh {} {}".format(base_repo, base_commit)
    print(cmd)
    fail = call(cmd, shell=True, executable='/bin/bash')


    # Send new message to next queue
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='127.0.0.1'))
    channel_out = connection.channel()
    channel_out.queue_declare(queue='production', durable=True)

    message = '{};{};{}'.format(pr_id, base_commit, commit)
    channel_out.basic_publish(
        exchange='',
        routing_key='production',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))


    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='pull_request', on_message_callback=callback)

channel.start_consuming()
