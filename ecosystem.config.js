module.exports = {
    apps: [
        {
            name: "saham-ai-api",
            script: "venv/bin/uvicorn",
            args: "scripts.api:app --host 0.0.0.0 --port 8000",
            interpreter: "none",
            cwd: "/home/ditoaryap/saham-ai",
            autorestart: true,
            watch: false,
            max_memory_restart: "1G",
            env: {
                NODE_ENV: "production",
            },
        },
    ],
};
