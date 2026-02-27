module.exports = {
    apps: [
        {
            name: "n8n",
            script: "n8n",
            args: "start",
            env: {
                N8N_HOST: "bot-saham.ditoaryap.my.id",
                N8N_PROTOCOL: "https",
                WEBHOOK_URL: "https://bot-saham.ditoaryap.my.id/",
                N8N_PORT: "5678"
            }
        }
    ]
};
