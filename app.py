import flask
from shelljob import proc

app = flask.Flask(__name__)


@app.route('/stream')
def stream():
    g = proc.Group()
    p = g.run(["bash", "-c", "./visage/acceptance_tests/command_files/docker-parallel-run.sh"])

    def read_process():
        while g.is_pending():
            lines = g.readlines()
            for proc, line in lines:
                yield line

    return flask.Response(read_process(), mimetype='text/plain')


if __name__ == "__main__":
    app.run(debug=True)
