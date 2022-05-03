FROM python:3.6

ADD python /python
RUN pip install prometheus_client
RUN pip install requests

WORKDIR /code
ENV PYTHONPATH '/python/'

CMD ["python" , "/python/veeamEnterpriseManager_exporter.py"]

EXPOSE 8000

