import elefast_example_fastapi_async

app = elefast_example_fastapi_async.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(f"{elefast_example_fastapi_async.__name__}:app")
