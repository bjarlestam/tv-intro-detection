from flask import Flask
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

@app.get("/health")
def index():
    return "<p>Up</p>"

@app.get("/intros/<pevi>")
def get_intros(pevi):
    return {
        "id": pevi,
        "startSeconds": 101,
        "endSeconds": 145,
    }

@app.post("/intros")
def intros():
    #TODO 
    # start a background thread that does the decoding
    # when decoding is done call the callbackUrl with intro data

    # We can use a with statement to ensure threads are cleaned up promptly
    with ThreadPoolExecutor(max_workers=5) as executor:
        print("submitting...")
        executor.submit(task, 'apa')

    return "OK"


def task(input_data):
    print("processed: %s" % input_data)
    return input_data

