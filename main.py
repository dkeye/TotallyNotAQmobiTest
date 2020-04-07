import argparse
import json
import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple
from urllib import parse, error, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s >> %(message)s')
logger = logging.getLogger(__name__)
EXCHANGES_ADDRESS = "https://www.cbr-xml-daily.ru/daily_json.js"

# Types
Params = Tuple[str, float]
Response = Tuple[int, str]


def validate_and_parse(query: str) -> Params:
    assert query, "params not specified"
    args = parse.parse_qs(query)
    # parse_qs return dict with lists in values like {key: ['value']}
    # here we do
    # if 'currency' in args and args['currency] not is None:
    #     currency = args['currency']"
    # else:
    #     raise AssertionError('reason')
    logger.debug("args %s", args)
    assert (currency := args.get('currency')) and (currency := currency[0]), "currency not specified"
    assert (value := args.get('value')) and (value := value[0]), "value not specified"
    try:
        value = float(value)
    except ValueError:
        raise AssertionError(f"value is not a number, value is '{value}'")
    return currency, value


def get_exchanges_rates(currency: str, trying: int = 3) -> float:
    currency = currency.upper()
    try:
        response = request.urlopen(EXCHANGES_ADDRESS).read()
        rates = json.loads(response)['Valute']
        assert (rate := rates.get(currency)) and (rate := rate['Value']), "no information on the rate of this currency"
        return float(rate)

    except error.HTTPError as e:
        time.sleep(1)
        if trying > 0:
            return get_exchanges_rates(currency, trying - 1)  # recursion
        e.args = (f"exchanges server error {e}, trying {trying}",)
        raise e

    except (json.JSONDecodeError, KeyError) as e:
        e.args = (f"exchanges server response decode error, {e} [{response[:500]}]",)
        raise e

    except ValueError as e:
        e.args = (f"rate converting error {e} [{rate}]",)
        raise e


def convert_handler(query: str) -> Response:
    try:
        logger.debug("query %s", query)
        currency, value = validate_and_parse(query)
    except AssertionError as e:
        logger.warning("validate params error: %s", str(e))
        reason = json.dumps({'reason': str(e)})
        return 400, reason

    try:
        rate = get_exchanges_rates(currency)
    except AssertionError as e:
        logger.warning(e)
        reason = json.dumps({'reason': str(e)})
        return 500, reason

    except Exception as e:
        logger.warning(e)
        reason = json.dumps({'reason': "exchanges server error is not available"})
        return 500, reason

    result_value = json.dumps({"value": value * rate})
    return 200, result_value


class Handlers(BaseHTTPRequestHandler):
    get_handlers = {
        "/convert": convert_handler,
    }

    def do_GET(self) -> None:
        parsed_url = parse.urlsplit(self.path)
        logger.debug("url %s", parsed_url)
        if not (handler := self.get_handlers.get(parsed_url.path)):
            self.reply(404)
            return

        response = handler(parsed_url.query)
        self.reply(*response)
        return

    def reply(self, status_code: int, message="") -> None:
        self.send_response(status_code)
        if message:
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(message.encode())
        else:
            self.end_headers()


def run(handler: BaseHTTPRequestHandler = Handlers, PORT: int = None) -> None:
    address = '', PORT
    with HTTPServer(address, handler) as httpd:
        print(f'Starting server, listening on: http://127.0.0.1:{PORT}/, use <Ctrl-C> to stop')
        httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="server port", type=int, default=8080)
    port = parser.parse_args().port
    run(PORT=port)
