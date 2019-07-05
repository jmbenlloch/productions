FROM ubuntu:16.04

RUN apt-get update && apt-get install git vim wget curl bzip2 gcc -y
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
RUN apt-get install git-lfs

RUN echo 'root:root' | chpasswd

#Add start script to run IC
ADD run_ic /software/run_ic
RUN chmod +x /software/run_ic

#Add user
RUN useradd -u 1001 -ms /bin/bash icuser
RUN echo 'icuser:icpass' | chpasswd
#Create directories
RUN mkdir -p /software/ /analysis_test
RUN chown icuser:icuser /software /analysis_test
USER icuser
WORKDIR /software

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda3.sh
RUN bash miniconda3.sh -b -p /software/miniconda3

RUN git clone REPOURL && cd REPONAME && git checkout -qf COMMITID

RUN /bin/bash -c "source /software/miniconda3/etc/profile.d/conda.sh; cd /software/REPONAME; source manage.sh install 3.7"
