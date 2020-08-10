from bs4 import BeautifulSoup

import requests
import asyncio
import time

domain_list = ['github.com',
               'github.global.ssl.fastly.net',
               'assets-cdn.github.com',
               'gist.github.com']

#ip_reg = r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"

LINUX_HOSTS_PATH = '/etc/hosts'
class AsynHttpProcessor:
    def __init__(self, url_list: list, num_of_cor:int = None, header:str = None):
        self._url_list = url_list
        self._header = header
        self._num_of_cor = len(self._url_list)
        self._loop = asyncio.get_event_loop()
        self._tasks = []
        self._exit_flag = False
        self._sleep_interval = 0.3

    async def http_get(self, url):
        response = requests.get(url, headers=self._header)
        self.process_rsp(url, response)

    def process_rsp(self, rsp_content):
        raise NotImplementedError

    def add_url(self, url):
        self._url_list.append(url)

    def _get_exit_flag(self):
        return self._exit_flag

    def set_exit_flag(self):
        self._exit_flag = True

    def start_forever(self, num_of_cor:int = None):
        if num_of_cor is not None:
            self._num_of_cor = num_of_cor
        i = 0
        while not self._get_exit_flag():
            if i < self._num_of_cor and len(self._url_list) > 0:
                i += 1
                url = self._url_list[0]
                self._url_list.pop(0)
                self._tasks.append(asyncio.ensure_future(self.http_get(url)))
                print(f'add {url}')
                continue
            if len(self._tasks) > 0:
                self._loop.run_until_complete(asyncio.wait(self._tasks))
            print(f'len of url list: {len(self._url_list)}, len of task:{len(self._tasks)}')
            i = 0
            self._tasks = []
            time.sleep(self._sleep_interval)
        self._loop.run_until_complete(asyncio.wait(self._tasks))
        self._loop.close()

    def start(self, num_of_cor:int = None):
        if num_of_cor is not None:
            self._num_of_cor = num_of_cor
        i = 0
        while len(self._url_list) >0:
            if i < self._num_of_cor:
                i += 1
                url = self._url_list[0]
                self._url_list.pop(0)
                self._tasks.append(asyncio.ensure_future(self.http_get(url)))
                print(f'add {url}')
                continue
            if len(self._tasks) > 0:
                self._loop.run_until_complete(asyncio.wait(self._tasks))
            self._tasks = []
            print(f'len of url list: {len(self._url_list)}, len of task:{len(self._tasks)}')
            i = 0
        self._loop.run_until_complete(asyncio.wait(self._tasks))
        self._loop.close()


class AsynHttpProcessorAsynQueue:
    def __init__(self, header:str = None):
        from asyncio import Queue
        self._url_queue = Queue()
        print(139)
        self._header = header
        self._num_of_cor = self._url_queue.qsize()
        self._loop = asyncio.get_event_loop()
        self._tasks = []
        self._exit_flag = False

    async def http_get(self, url):
        response = requests.get(url, headers=self._header)
        self.process_rsp(url, response)

    def process_rsp(self, rsp_content):
        raise NotImplementedError

    async def add_url(self, url):
        await self._url_queue.put(url)

    def _get_exit_flag(self):
        return self._exit_flag

    def set_exit_flag(self):
        self._exit_flag = True

    async def start_forever(self, num_of_cor:int = None):
        if num_of_cor is not None:
            self._num_of_cor = num_of_cor
        i = 0
        while not self._get_exit_flag():
            url = await self._url_queue.get()
            if i < self._num_of_cor and self._url_queue.qsize() > 0:
                i += 1
                self._tasks.append(asyncio.ensure_future(self.http_get(url)))
                print(f'add {url}')
                continue
            #if self._url_queue.qsize() > 0:
            print(174,len(self._tasks))
            if len(self._tasks) > 0:
                self._loop.run_until_complete(asyncio.wait(self._tasks))
            print(f'len of url queue: {self._url_queue.qsize()}, len of task:{len(self._tasks)}')
            i = 0
            self._tasks = []
        self._loop.run_until_complete(asyncio.wait(self._tasks))
        self._loop.close()


    #def start(self, num_of_cor:int = None):
    #    if num_of_cor is not None:
    #        self._num_of_cor = num_of_cor
    #    i = 0G
    #    while len(self._url_list) >0:
    #        if i < self._num_of_cor:
    #            i += 1
    #            url = self._url_list[0]
    #            self._url_list.pop(0)
    #            self._tasks.append(asyncio.ensure_future(self.http_get(url)))
    #            print(f'add {url}')
    #            continue
    #        if len(self._tasks) > 0:
    #            self._loop.run_until_complete(asyncio.wait(self._tasks))
    #        self._tasks = []
    #        print(f'len of url list: {len(self._url_list)}, len of task:{len(self._tasks)}')
    #        i = 0
    #    self._loop.run_until_complete(asyncio.wait(self._tasks))
    #    self._loop.close()

class DomainNameParser(AsynHttpProcessor):
    def __init__(self,domain_name_list, header:str = None):
        self._domain_dict = {}
        self._dns_dict = {}
        url_list = []
        for domain_name in domain_name_list:
            url = self.compose_url(domain_name)
            self._domain_dict.update({domain_name:url})
            url_list.append(url)

        AsynHttpProcessor.__init__(self, url_list, header)

    def compose_url(self, domain_name):
        domain_parts = domain_name.split('.')
        assert (len(domain_parts) >= 2)
        if len(domain_parts) == 2:
            return f'https://{".".join(domain_parts[-2:])}.ipaddress.com'
        else:
            return f'https://{".".join(domain_parts[-2:])}.ipaddress.com/{domain_name}'

    def process_rsp(self,url, response):
        rsp_content = response.content
        for domain_name ,domain_url in self._domain_dict.items():
            if domain_url == url:
                break
        find_str = f'{domain_name[1:]} resolves to the'
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
                    print(f"{domain_name} IP: {ip}")
                    self._dns_dict.update({domain_name: ip})
                    return
    def get_dns_dict(self):
        return self._dns_dict


class DomainNameParserAsynQueue(AsynHttpProcessorAsynQueue):
    def __init__(self, header:str = None):
        self._domain_dict = {}
        self._dns_dict = {}

        AsynHttpProcessorAsynQueue.__init__(self, header)

    def compose_url(self, domain_name):
        domain_parts = domain_name.split('.')
        assert (len(domain_parts) >= 2)
        if len(domain_parts) == 2:
            return f'https://{".".join(domain_parts[-2:])}.ipaddress.com'
        else:
            return f'https://{".".join(domain_parts[-2:])}.ipaddress.com/{domain_name}'

    async def add_domain(self,domain):
        for domain in domain_list:
            url = self.compose_url(domain)
            self._domain_dict.update({domain:url})
            await self.add_url(url)

    def process_rsp(self,url, response):
        rsp_content = response.content
        for domain_name ,domain_url in self._domain_dict.items():
            if domain_url == url:
                break
        find_str = f'{domain_name[1:]} resolves to the'
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
                    print(f"{domain_name} IP: {ip}")
                    self._dns_dict.update({domain_name: ip})
                    return
    def get_dns_dict(self):
        return self._dns_dict

async def main2():
    domain_name_parser = DomainNameParserAsynQueue()
    for domain in domain_list:
        await domain_name_parser.add_domain(domain)
    await domain_name_parser.start_forever(1)
    print(domain_name_parser.get_dns_dict())


def ModifyHostFile(dnsDictIn):
    import os
    import re
    import sys
    dnsDict = {k:v for k, v in dnsDictIn.items()}
    euid = os.geteuid()
    if euid != 0:
        print("Script not started as root. Running sudo..")
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        # the next line replaces the currently-running process with the sudo
        os.execlpe('sudo', *args)

    print('Running. Your euid is', euid)

    with open(LINUX_HOSTS_PATH ,'r+') as fh:
        lines = fh.readlines()
    for i, line in enumerate(lines):
        loc = line.find('#')
        #print(f"line: {line}, LOC:{loc}")
        content =  line if loc == -1 else line[:loc]
        for domainName, ip in dnsDict.items():
            dnLoc = content.lower().find(domainName.lower())
            if dnLoc >= 0:
                content = f'{ip}\t{content[dnLoc:]}'
                del dnsDict[domainName]
                break
        if loc == -1:
            line = content
        else:
            line = content + line[loc:]
        lines[i] = line

    for domainName, ip in dnsDict.items():
        lines.append(f'{ip}\t{domainName}\n')
    with open(LINUX_HOSTS_PATH,'w+') as fh:
        fh.writelines(lines)




def main3():
    domain_name_parser = DomainNameParser(domain_list)
    domain_name_parser.start()
    dnsDict = domain_name_parser.get_dns_dict()
    ModifyHostFile(dnsDictIn=dnsDict)

if __name__ == '__main__':
    #import nest_asyncio

    #nest_asyncio.apply()

    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(main2())
    #loop.close()

    main3()
    #ModifyHostFile({'www.kimme.cn':'192.168.1.1',
    #                'gist.github.com':'140.82.112.499'})


