# TotallyNotAQmobiTest

To start test:
  * python test.py
  
To start server:

  * python main.py [--port PORT]

To start server in Docker:
  * check params like port and image name in start.sh
  * start start.sh

Now you can send requests to [`localhost:8080`](http://localhost:8080)

Convert eur to rub example:

  http://localhost:8080/convert?currency=eur&value=1
  
    {"value": 82.012}
