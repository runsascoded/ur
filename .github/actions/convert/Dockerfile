FROM python:3.8
RUN pip install --upgrade pip requests
#ADD ./convert.py .
ENTRYPOINT ["python",".github/actions/convert/convert.py"]