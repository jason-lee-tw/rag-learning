import os

import dotenv
import uvicorn

from server_config.tracer import register_phoenix_tracer


def main():
  dotenv.load_dotenv()
  register_phoenix_tracer()
  port = int(os.getenv('PORT', '3001'))
  reload = os.getenv('RELOAD', 'false').lower() == 'true'
  uvicorn.run(
    'server_config.server:start_app',
    factory=True,
    host='0.0.0.0',
    port=port,
    reload=reload,
  )


if __name__ == '__main__':
  main()
