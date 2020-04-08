import argparse
import json
import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple, NewType
from urllib import parse, error, request

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s:%(funcName)s >> %(message)s')
logger = logging.getLogger(__name__)
EXCHANGES_ADDRESS = "https://www.cbr-xml-daily.ru/daily_json.js"

# Types
Params = Tuple[str, float]
Response = Tuple[int, str]
EResponse = NewType('EResponse', str)


def validate_and_parse(query: str) -> (Params, str):
    result, reason = (), ""
    try:
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
        value = float(value)
    except AssertionError as e:
        reason = str(e)
    except ValueError:
        reason = f"value is not a number, value is '{value}'"
    else:
        result = currency, value
    return result, reason


def get_exchanges_rates(trying: int = 3) -> (EResponse, str):
    result, reason = "", ""
    try:
        result = request.urlopen(EXCHANGES_ADDRESS).read()
    except error.HTTPError as e:
        logger.warning("exchanges server is not available %s", e)
        time.sleep(1)
        if trying > 0:
            return get_exchanges_rates(trying - 1)  # recursion
        reason = f"exchanges server error {e}, trying {trying}"
    return EResponse(result), reason


def get_currency_rate(currency: str, exchanges_response: EResponse) -> (float, str):
    result, reason = 0.0, ""
    currency = currency.upper()
    try:
        rates = json.loads(exchanges_response)['Valute']
        assert (rate := rates.get(currency)) and (rate := rate['Value']), "no information on the rate of this currency"
        result = float(rate)

    except (json.JSONDecodeError, KeyError) as e:
        reason = f"exchanges server response decode error, {e} [{exchanges_response[:500]}]"
    except AssertionError as e:
        reason = str(e)
    except ValueError as e:
        reason = f"rate converting error {e} [{rate}]"

    return result, reason


def convert_handler(query: str) -> Response:
    logger.debug("query %s", query)
    params, reason = validate_and_parse(query)

    if not params:
        logger.warning("validate params error: %s", reason)
        reason = json.dumps({'reason': reason})
        return 400, reason

    currency, value = params
    exchanges_response, reason = get_exchanges_rates(3)
    if not exchanges_response:
        logger.warning(reason)
        reason = json.dumps({'reason': reason})
        return 500, reason

    rate, reason = get_currency_rate(currency, exchanges_response)
    if not rate:
        logger.warning(reason)
        reason = json.dumps({'reason': reason})
        return 500, reason

    result_value = json.dumps({"value": value * rate})
    return 200, result_value


class Handlers(BaseHTTPRequestHandler):
    get_handlers = {
        "/convert": convert_handler,
    }

    def do_GET(self) -> None:
        parsed_url = parse.urlsplit(self.path)
        logger.info("url %s", parsed_url)
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
