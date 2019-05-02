
from datetime import datetime, timedelta
import requests

class ShigarakiLoader:

    def __init__(self, proxy_host, proxy_port):
        self.proxy_host = proxy_host
        self. proxy_port = proxy_port
        self.url_base = ('http://database.rish.kyoto-u.ac.jp'
                         '/arch/mudb/data/ionosonde/text')

    def saveTo(self, directory, start, end):
        if not (directory.endswith('/') or directory.endswith('\\')):
            directory += '/'

        n_files = 0
        start = start + timedelta(hours = 9)
        end = end + timedelta(hours = 9)
        if end > start:
            dates = set()
            delta = end - start

            for day in range(delta.days+1):
                date = start.replace(hour=0, minute=0, second=0) + timedelta(days=day)
                for hour in range(24):
                    for minute in (x*15 for x in range(5)):
                        new_dt = date + timedelta(hours=hour) + timedelta(minutes=minute)
                        if new_dt >= start and new_dt <= end:
                            dates.add(new_dt)

            dates = list(dates)
            dates.sort()

            for date in dates:
                year = date.year
                month = date.month
                day = date.day
                hour = date.hour
                minute = date.minute
                format = (
                    '{:s}'
                    '/{:d}'
                    '/{:d}{:02d}'
                    '/{:d}{:02d}{:02d}'
                    '/{:d}{:02d}{:02d}{:02d}{:02d}'
                    '{:s}')
                url = format.format(
                    self.url_base,
                    year,
                    year, month,
                    year, month, day,
                    year, month, day, hour, minute,
                    '_ionogram.txt')

                if self.proxy_host and self.proxy_port:
                    proxies = {
                        'http': '{}:{}'.format(self.proxy_host, self.proxy_port)
                    }
                    r = requests.get(url, proxies=proxies)
                else:
                    r = requests.get(url)

                if r.status_code == 200:
                    format = (
                        '{:d}{:02d}{:02d}{:02d}{:02d}'
                        '{:s}')
                    filename = directory + format.format(
                        year, month, day, hour, minute,
                        '_ionogram.txt')

                    with open(filename, 'w') as file:
                        file.write(r.text)

                    n_files += 1

        return n_files

