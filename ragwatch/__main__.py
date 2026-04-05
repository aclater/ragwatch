import uvicorn

if __name__ == "__main__":
    uvicorn.run("ragwatch:app", host="0.0.0.0", port=9090, reload=False)
