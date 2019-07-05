#!/usr/bin/env python
import pika
import time
from subprocess import call
from glob import glob
from os import path
import os


def checkmakedir( path ):
    if os.path.isdir( path ):
        print('hey, directory already exists!: {}'.format(path))
    else:
        os.makedirs( path )
        print('creating directory... {}'.format(path))

def get_file_number(fname):
    return int(fname.split('.')[-2].split('_')[0])


# Define paths and templates
input_files = "/analysis_test/MC/NEW/NEXT_v1_05_02/Xe0nu/ACTIVE/irene/output/*h5"
input_files = glob(input_files)
exe_template = open('/home/jmbenlloch/server/templates/exe_ic_docker.sh').read()
cfg_template = open('/home/jmbenlloch/server/templates/penthesilea.conf').read()


# RabbitMQ connection
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='127.0.0.1'))
channel = connection.channel()

channel.queue_declare(queue='production', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


def create_jobs(pr_id, commit_id):
    base_path = "/analysis_test/MC/NEW/NEXT_v1_05_02/Xe0nu/ACTIVE/penthesilea/"
    base_path = path.join(base_path, commit_id)

    job_dir = base_path + '/jobs/'
    cfg_dir = base_path + '/configs/'
    log_dir = base_path + '/logs/'
    out_dir = base_path + '/output/'
    checkmakedir (job_dir)
    checkmakedir (cfg_dir)
    checkmakedir (log_dir)
    checkmakedir (out_dir)

    pending_jobs = []

    nfiles = 2
    for f in input_files[:nfiles]:
        index = get_file_number(f)
        fname = f.split('/')[-1]

        basename = fname.replace('pmaps', 'hdst')
        basename = '.'.join(basename.split('.')[0:-1])

        cfg_fname = cfg_dir + '{0}.conf'.format(basename)
        job_fname = job_dir + '{0}.sh'  .format(basename)
        fileout   = out_dir + '{0}.h5'  .format(basename)

        stderr = log_dir + '/' + basename + '.err'
        stdout = log_dir + '/' + basename + '.out'
        log    = log_dir + '/' + basename + '.log'

        parameters = {
            'stdout' : stdout,
            'stderr' : stderr,
            'filein' : f,
            'fileout': fileout,
            'config' : cfg_fname,
            'jobname': fileout,
            'repo'   : 'testprod',
            'tag'    : commit_id,
            'city'   : 'penthesilea',
            'pr_id'  : pr_id,
            'commit' : commit_id,
            'job'    : job_fname,
        }

        with open(job_fname, 'w') as exe_file:
            exe_file.write(exe_template.format(**parameters))
        pending_jobs.append(job_fname)

        with open(cfg_fname, 'w') as cfg_file:
            cfg_file.write(cfg_template.format(**parameters))

    send_jobs(pending_jobs)


def callback(ch, method, properties, body):
    print(" [x] Received {}".format(body))
    pr_id, base_commit, commit = body.decode().split(';')

    create_jobs(pr_id, base_commit)
    create_jobs(pr_id, commit)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def send_jobs(jobs):
    for job in jobs:
        cmd = "qsub {}".format(job)
        print(cmd)
        call(cmd, shell=True, executable='/bin/bash')


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='production', on_message_callback=callback)

channel.start_consuming()
