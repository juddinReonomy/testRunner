
import flask
import subprocess

from gevent.pywsgi import WSGIServer
from gevent.select import select

app = flask.Flask(__name__)


@app.route('/yield')
def index():
    def inner():
        proc = subprocess.Popen(
            ['/home/ubuntu/visage/acceptance_tests/command_files/cucumber-command-prod.sh'],
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


http_server = WSGIServer(('', 5000), app)
http_server.serve_forever()






















# import flask
# from flask import render_template
# from shelljob import proc
#
# app = flask.Flask(__name__)
#
#
# @app.route('/run_on_prod')
# def stream():
#     g = proc.Group()
#     p = g.run(["bash", "-c", "/home/ubuntu/visage/acceptance_tests/command_files/cucumber-command-prod.sh"])
#
#     def read_process():
#         while g.is_pending():
#             lines = g.readlines()
#             for proc, line in lines:
#                 yield line
#
#     return flask.Response(read_process(), mimetype='text/plain')
#
#
# @app.route('/status')
# def status():
#     return {"Message": "ok"}, 200
#
#
# @app.route('/report')
# def report():
#     return render_template("report.html")
#
#
# if __name__ == "__main__":
#     app.run(host='0.0.0.0')
