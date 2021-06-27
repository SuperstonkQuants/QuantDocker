ARG BASE_CONTAINER=jupyter/all-spark-notebook
FROM $BASE_CONTAINER

USER root

# RSpark config
ENV R_LIBS_USER "${SPARK_HOME}/R/lib"
RUN fix-permissions "${R_LIBS_USER}"



# R pre-requisites
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \ 
    fonts-dejavu \
    gfortran \
    gcc \
    g++ \
    software-properties-common

USER ${NB_UID}

# R packages including IRKernel which gets installed globally.
RUN mamba install --quiet --yes \
    'r-base=4.1.0' \
    'r-ggplot2=3.3*' \
    'r-irkernel=1.2*' \
    'r-rcurl=1.98*' \
    'r-sparklyr=1.7*' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# Spylon-kernel
RUN mamba install --quiet --yes 'spylon-kernel=0.4*' && \
    mamba clean --all -f -y && \
    python -m spylon_kernel install --sys-prefix && \
    rm -rf "/home/${NB_USER}/.local" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"
    
# Install Tensorflow
RUN mamba install --quiet --yes \
    'tensorflow=2.4.1' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

RUN pip install --upgrade pip && pip --no-cache-dir install poetry
    

COPY ./requirements.txt .

RUN pip install -r requirements.txt

