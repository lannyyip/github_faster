from bs4 import BeautifulSoup

import requests
import asyncio

domain_list = ['github.com',
                'github.global.ssl.fastly.net',
               'assets-cdn.github.com']

#ip_reg = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"

class DomainParser:
    def __init__(self, domain_name,dns_dict):
        self._dns_dict = dns_dict
        self._domain_name = domain_name
        self._url = self.compose_url()

    def compose_url(self):
        domain_parts = self._domain_name.split('.')
        assert(len(domain_parts)>=2)
        if len(domain_parts) == 2:
            return f'https://{".".join(domain_parts[-2:])}.ipaddress.com'
        else:
            return f'https://{".".join(domain_parts[-2:])}.ipaddress.com/{self._domain_name}'

    async def crawler(self):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        response = requests.get(self._url, headers=headers)

        self.parse_rsp(response.content)

    def parse_rsp(self, rsp_content):
        find_str = f'{self._domain_name[1:]} resolves to the'
        soup = BeautifulSoup(rsp_content, 'html.parser', from_encoding='utf-8')
        divs = soup.find_all(name='div')
        for div in divs:
            found = False
            for item in div.strings:
                if not found and item.find(find_str) != -1:
                    found = True
                    continue
                if found:
                    ip = item
                    print(f"{self._domain_name} IP: {ip}")
                    self._dns_dict.update({self._domain_name: ip})
                    return


if __name__ == '__main__':
    dns_list = []
    dns_dict = {}
    for domain in domain_list:
        dns_list.append(DomainParser(domain,dns_dict))
    loop = asyncio.get_event_loop()
    tasks = []
    for t in dns_list:
        tasks.append(asyncio.ensure_future(t.crawler()))

    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    print(dns_dict)
    #TODO: update the hosts file with the DNS info


