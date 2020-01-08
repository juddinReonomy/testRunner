from flask import render_template
from gevent.select import select

import flask
import subprocess

app = flask.Flask(__name__)


@app.route('/prod-smoke')
def index():
    def inner():
        proc = subprocess.Popen(
            ['cd /home/ubuntu/visage/acceptance_tests/; git pll; cd /home/ubuntu/testRunner; git pull; cd '
             '/home/ubuntu/visage/acceptance_tests; bundle install'],
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


@app.route('/report')
def report():
    return render_template("report.html")


@app.route('/status')
def status():
    return {"Message": "ok"}, 200


if __name__ == "__main__":
    app.run(host='0.0.0.0')
