from fastapi import FastAPI
import tensorflow as tf
import langchain
import llama_index

app = FastAPI()

@app.get("/versions")
def versions():
    return {
        "tensorflow": tf.__version__,
        "langchain": langchain.__version__,
        "llama_index": llama_index.__version__,
    }
