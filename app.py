import flask
from flask import render_template
from shelljob import proc

app = flask.Flask(__name__)


@app.route('/stream')
def stream():
    g = proc.Group()
    p = g.run(["bash", "-c", "/home/ubuntu/visage/acceptance_tests/command_files/cucumber-command-prod.sh"])

    def read_process():
        while g.is_pending():
            lines = g.readlines()
            for proc, line in lines:
                yield line

    return flask.Response(read_process(), mimetype='text/plain')


@app.route('/report')
def report():
    return render_template('/home/ubuntu/visage/acceptance_tests/build/reports/report.html', title='report')


@app.route('/status')
def status():
    return {"Message": "ok"}, 200


if __name__ == "__main__":
    app.run(debug=True)
