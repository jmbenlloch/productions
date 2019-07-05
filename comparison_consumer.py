import tables as tb
import numpy as np
from os import path
import os
import matplotlib.pylab as plt
from glob import glob
import pika

import pdb

def checkmakedir( path ):
    if os.path.isdir( path ):
        print('hey, directory already exists!: {}'.format(path))
    else:
        os.makedirs( path )
        print('creating directory... {}'.format(path))


def get_hits_energies(files):
    for f in files:
        energies = []
        try:
            with tb.open_file(f) as h5in:
                energies.append(h5in.root.RECO.Events.cols.E[:])
        except:
            pass

    energies = np.concatenate(energies)
    return energies


def process_production(commit1, commit2):
    base_path = '/analysis_test/MC/NEW/NEXT_v1_05_02/Xe0nu/ACTIVE/penthesilea/{}/output/*h5'.format(commit1)
    files = glob(base_path)
    energies1 = get_hits_energies(files)

    base_path = '/analysis_test/MC/NEW/NEXT_v1_05_02/Xe0nu/ACTIVE/penthesilea/{}/output/*h5'.format(commit2)
    files = glob(base_path)
    energies2 = get_hits_energies(files)

    return energies1, energies2


# RabbitMQ connection
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='127.0.0.1'))
channel = connection.channel()

channel.queue_declare(queue='comparison', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


def produce_report(pr_id, base_commit, commit):
    energies1, energies2 = process_production(base_commit, commit)

    mean_energy1 = energies1.mean()
    mean_energy2 = energies2.mean()

    result = 'Failure'
    color  = 'red'
    success = (mean_energy2 > 0.9 * mean_energy1) and (mean_energy2 < 1.1 * mean_energy1)
    if success:
        result = 'Success!'
        color  = 'green'

    report_template = open('/home/jmbenlloch/server/templates/result.html').read()
    base_dir = '/var/www/html/pull_requests/{}'.format(pr_id)
    checkmakedir(base_dir)

    report_fname = path.join(base_dir, '{}.html'.format(commit))
    hist_fname   = path.join(base_dir, '{}.png' .format(commit))

    plt.figure()
    plt.hist(energies1, label='master', alpha=0.5)
    plt.hist(energies2, label='PR', alpha=0.5)
    plt.legend(loc='upper right')
    plt.savefig(hist_fname)

    parameters = {'pr_id' : pr_id,
                  'commit' : commit,
                  'result' : result,
                  'color'  : color,
                  'img'    : hist_fname.split('/')[-1]}

    with open(report_fname, 'w') as report_file:
        report_file.write(report_template.format(**parameters))

    return success, report_fname



def callback(ch, method, properties, body):
    print(" [x] Received {}".format(body))
    pr_id, base_commit, commit = body.decode().split(';')

    success, report_fname = produce_report(pr_id, base_commit, commit)

    # Send new message to next queue
    channel_out = connection.channel()
    channel_out.queue_declare(queue='finished', durable=True)

    message = '{};{};{}'.format(pr_id, success, report_fname)
    channel_out.basic_publish(
        exchange='',
        routing_key='finished',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))


    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='comparison', on_message_callback=callback)

channel.start_consuming()
