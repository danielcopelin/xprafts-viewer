from python:3.6-alpine

MAINTAINER danielcopelin@gmail.com

COPY . /code
WORKDIR /code

RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk --no-cache --update-cache add \
    gcc gfortran build-base wget \
    freetype-dev libpng-dev openblas-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install pipenv

RUN pipenv install --system --deploy --ignore-pipfile

CMD ["python", "app.py"]