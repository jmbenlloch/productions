#!/bin/bash
#PBS -N {jobname}
#PBS -q short
#PBS -o {stdout}
#PBS -e {stderr}
#PBS -M jmbenlloch@ific.uv.es

echo date
date

docker run -v /analysis_test:/analysis_test nextic/{repo}:{tag} /software/run_ic {city} {config}

echo date
date

curl -X POST -H 'Content-Type: application/json' --data '{{"pr": "{pr_id}", "job": "{job}", "commit": "{commit}"}}' http://localhost:8080/jobs
