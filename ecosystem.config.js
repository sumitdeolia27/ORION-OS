module.exports = {
  apps: [
    {
      name: 'orion-backend',
      script: 'scripts/api_server.py',
      interpreter: 'python3',
      env: {
        ORION_DISABLE_TTS: '1',
        PORT: '5000'
      },
      restart_delay: 5000,
      max_restarts: 10,
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'orion-frontend',
      script: 'npm',
      args: 'start',
      env: {
        PORT: '3000',
        NODE_ENV: 'production'
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    }
  ]
}
