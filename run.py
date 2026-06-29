from app import create_app

app = create_app()

if __name__ == "__main__":
    # 0.0.0.0 so it's reachable inside Docker/Kubernetes, not just localhost
    app.run(host="0.0.0.0", port=8080)
