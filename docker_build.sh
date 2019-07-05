#|/bin/bash

if [ $# -lt 2 ]; then
	echo "Error: missing arguments"
	echo "Usage: bash docker_build.sh REPO_URL COMMIT_ID"
	exit
fi

REPO=$1
COMMIT=$2
REPONAME=`echo $REPO | rev | cut -d'/' -f1 | rev`


docker pull nextic/$REPONAME:$COMMIT

if [ $? -eq 0 ]; then
	exit; # the image is already in the registry and pulled
fi

TEMPLATES="/home/jmbenlloch/server/docker"
BASEDIR="/home/jmbenlloch/server/builds"
BUILDIR=$BASEDIR/$COMMIT

echo $BUILDIR
mkdir $BUILDIR

cp $TEMPLATES/Dockerfile $BUILDIR
cp $TEMPLATES/run_ic $BUILDIR

sed -i "s|REPOURL|$REPO|g" $BUILDIR/Dockerfile
sed -i "s|COMMITID|$COMMIT|g" $BUILDIR/Dockerfile
sed -i "s|REPONAME|$REPONAME|g" $BUILDIR/Dockerfile
sed -i "s|REPONAME|$REPONAME|g" $BUILDIR/run_ic

cd $BUILDIR

TAG="ic_$COMMIT"
docker build . -t $TAG
docker tag $TAG nextic/$REPONAME:$COMMIT
docker push nextic/$REPONAME:$COMMIT
