from fastapi import FastAPI

app = FastAPI(

    title="MATANGI AI SERVER",

    version="1.0.0"

)


@app.get("/")

def root():

    return {

        "success": True,

        "message": "MATANGI AI SERVER is running."

    }