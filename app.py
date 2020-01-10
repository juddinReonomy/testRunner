from flask import render_template
from gevent.select import select
import requests
import flask
import subprocess
from datetime import datetime
from pytz import timezone
import os

app = flask.Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
now = datetime.now(timezone('US/Eastern'))
dt_time = now.strftime("%B-%d-%Y_%I-%M-%p")


@app.route('/prod-smoke')
def index():
    proc = subprocess.Popen(
        ['cd /home/ubuntu/visage/acceptance_tests/; echo "vistage - pulling from master.."; git pull; cd '
         '/home/ubuntu/testRunner; echo "testRunner - pull from master.."; git pull; cd '
         '/home/ubuntu/visage/acceptance_tests; echo "acceptance_tests - updating all dependencies.."; bundle '
         'install; cd /home/ubuntu/visage/acceptance_tests/; bundle '
         'exec cucumber TEST_ENV=prod '
         'BROWSER=headless-chrome --tags @production -f pretty -f html -o '
         '/home/ubuntu/testRunner/templates/"%s"_report.html -f pretty -f json -o '
         '/home/ubuntu/testRunner/templates/json_report.json' % dt_time],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # slack message send
    payload = "{\"text\":\"Test started after production release. Here is the Report: " \
              "http://prd-qa.internal.reonomy.com:5000/%s_report after 10 seconds refresh browser to see progress" \
              "it should take 5+ minutes to complete\"} " % dt_time
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request('POST', 'provide_webwook_url',
                                headers=headers, data=payload)
    return "Production post validation test is running...check slack channel #prod-tests"


@app.route('/prod-smoke_manual_visit')
def smoke_manual_visit():
    def inner():
        proc = subprocess.Popen(
            ['cd /home/ubuntu/visage/acceptance_tests/; echo "vistage - pulling from master.."; git pull; cd '
             '/home/ubuntu/testRunner; echo "testRunner - pull from master.."; git pull; cd '
             '/home/ubuntu/visage/acceptance_tests; echo "acceptance_tests - updating all dependencies.."; bundle '
             'install; cd /home/ubuntu/visage/acceptance_tests/; bundle '
             'exec cucumber TEST_ENV=prod '
             'BROWSER=headless-chrome --tags @production -f pretty -f html -o '
             '/home/ubuntu/testRunner/templates/"%s"_report.html -f pretty -f '
             'json -o '
             '/home/ubuntu/testRunner/templates/json_report.json' % dt_time],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # pass data until client disconnects, then terminate
        try:
            awaiting = [proc.stdout, proc.stderr]
            while awaiting:
                # wait for output on one or more pipes, or for proc to close a pipe
                ready, _, _ = select(awaiting, [], [])
                for pipe in ready:
                    line = pipe.readline()
                    if line:
                        # some output to report
                        print
                        "sending line:", line.replace('\n', '\\n')
                        yield line.rstrip() + '<br/>\n'
                    else:
                        # EOF, pipe was closed by proc
                        awaiting.remove(pipe)
            if proc.poll() is None:
                print
                "process closed stdout and stderr but didn't terminate; terminating now."
                proc.terminate()

        except GeneratorExit:
            # occurs when new output is yielded to a disconnected client
            print
            'client disconnected, killing process'
            proc.terminate()

        # wait for proc to finish and get return code
        ret_code = proc.wait()
        print
        "process return code:", ret_code

    return flask.Response(inner(), mimetype='text/html')


@app.route('/report', methods=['GET'])
def report():
    return render_template("report.html")


@app.route('/better_report', methods=['GET'])
def better_report():
    os.system('ruby /home/ubuntu/testRunner/ruby_script_for_report.rb')
    return render_template("my_test_report.html")


@app.route('/status')
def status():
    return {"Message": "ok"}, 200


@app.route('/<string:page_name>/')
def render_static(page_name):
    return render_template('%s.html' % page_name)


@app.route('/history')
def homepage():
    path = os.getcwd() + "/templates"
    list_of_files = {}

    for filename in os.listdir(path):
        if filename.endswith('.html'):
            list_of_files[filename] = "http://prd-qa.internal.reonomy.com:5000/" + filename
    # return list_of_files
    return render_template('index.html', list_of_files=list_of_files)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
