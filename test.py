import unittest
from main import validate_and_parse, get_currency_rate, Handlers, EResponse


class ConvertTest(unittest.TestCase):
    def test_check_path(self):
        nullpath = ''
        badpath = 'asdfc'
        rightpath = 'convert'

        class Url(Handlers):
            address = 'http://bla-bla.com/'

            def __init__(self, path):
                self.path = self.address + path

            def reply(self, status_code: int, message=""):
                return status_code, message

        self.assertEqual(Handlers.do_GET(Url(nullpath)), (404, ''))
        self.assertEqual(Handlers.do_GET(Url(badpath)), (404, ''))
        self.assertEqual(Handlers.do_GET(Url(rightpath)), (400, '{"reason": "params not specified"}'))

    def test_args_parse(self):
        nullargs = ''
        badargs1 = 'currency=&value=10'
        badargs2 = 'currency=usd&value='
        badargs3 = 'currency=usd&value=dfsd'
        badargs4 = 'currency=1&value=1'
        goodargs = 'currency=usd&value=1'

        self.assertEqual(validate_and_parse(nullargs), ((), "params not specified"))
        self.assertEqual(validate_and_parse(badargs1), ((), "currency not specified"))
        self.assertEqual(validate_and_parse(badargs2), ((), "value not specified"))
        self.assertEqual(validate_and_parse(badargs3), ((), "value is not a number, value is 'dfsd'"))
        self.assertEqual(validate_and_parse(badargs4), ((), "wrong currency"))
        self.assertEqual(validate_and_parse(goodargs), (('usd', 1.0), ""))
        pass

    def test_rates_parse(self):
        nullargs1 = EResponse('')
        nullargs2 = EResponse('{}')
        badargs1 = EResponse('{"fvsd": 1}')
        badargs2 = EResponse('{"Valute": {}}')
        badargs3 = EResponse('{"Valute": {"VSD": {}}}')
        badargs4 = EResponse('{"Valute": {"USD": {}}}')
        badargs5 = EResponse('{"Valute": {"USD": {"Value": "edfd"}}}')
        goodargs = EResponse('{"Valute": {"USD": {"Value": 75.0}}}')

        self.assertEqual(get_currency_rate("usd", nullargs1)[0], 0.0)
        self.assertEqual(get_currency_rate("usd", nullargs2)[0], 0.0)
        self.assertEqual(get_currency_rate("usd", badargs1)[0], 0.0)
        self.assertEqual(get_currency_rate("usd", badargs2)[0], 0.0)
        self.assertEqual(get_currency_rate("usd", badargs3)[0], 0.0)
        self.assertEqual(get_currency_rate("usd", badargs4)[0], 0.0)
        self.assertEqual(get_currency_rate("usd", badargs5)[0], 0.0)
        self.assertNotEqual(get_currency_rate("usd", goodargs), 0.0)


if __name__ == '__main__':
    unittest.main()
