#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Components.config import config
from enigma import getDesktop
from os.path import isdir, exists, realpath, dirname, join, isfile
from os import system, stat, statvfs, listdir, remove, chmod, popen
from random import choice
import base64
import datetime
import html
import html.entities
import re
import requests
import ssl
import sys
import unicodedata

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning)

screenwidth = getDesktop(0).size()
PY3 = True

try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch


def u(x):
    return x if isinstance(x, str) else x.decode('utf-8')


def unicodify(s, encoding='utf-8', norm=None):
    if not isinstance(s, str):
        s = str(s, encoding)
    if norm:
        s = unicodedata.normalize(norm, s)
    return s


def installed(plugin_name):
    from Tools.Directories import resolveFilename, SCOPE_PLUGINS
    path = resolveFilename(SCOPE_PLUGINS, "Extensions/" + plugin_name)
    return exists(path)


def checktoken(token):
    result = base64.b64decode(token)
    result = base64.b64decode(result)
    result = base64.b64decode(result).decode()
    return result


def getEncodedString(value):
    returnValue = ""
    try:
        returnValue = value.encode("utf-8", 'ignore')
    except UnicodeDecodeError:
        try:
            returnValue = value.encode("iso8859-1", 'ignore')
        except UnicodeDecodeError:
            try:
                returnValue = value.decode("cp1252").encode("utf-8")
            except UnicodeDecodeError:
                returnValue = b"n/a"
    return returnValue


def ensure_str(s, encoding="utf-8", errors="strict"):
    if isinstance(s, str):
        return s
    if isinstance(s, bytes):
        return s.decode(encoding, errors)
    raise TypeError(f"not expecting type '{type(s)}'")


_ESCAPE_RE = re.compile(r"[&<>\"']")
_UNESCAPE_RE = re.compile(r"&\s*(#?)(\w+?)\s*;")
_ESCAPE_DICT = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}


def get_mediafire_direct_url(page_url):
    """Estrae l'URL diretto di download da una pagina MediaFire"""
    html = getUrl(page_url)
    if not html:
        return None

    # Cerca il link con data-scrambled-url
    match = re.search(r'data-scrambled-url="([^"]+)"', html)
    if match:
        scrambled = match.group(1)
        direct = base64.b64decode(scrambled).decode('utf-8')
        return direct

    # Fallback: cerca il link di download normale
    match = re.search(r'href="(https://download[^"]+)"', html)
    if match:
        return match.group(1)

    # Fallback: cerca il bottone "Click to download"
    match = re.search(
        r'<a[^>]+href="([^"]+)"[^>]+class="input[^"]*download[^"]*"',
        html)
    if match:
        return match.group(1)

    return None


def html_escape(value):
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_DICT[m.group(0)], value.strip())


def html_unescape(value):
    def convert_entity(m):
        if m.group(1) == "#":
            try:
                if m.group(2)[:1].lower() == "x":
                    return chr(int(m.group(2)[1:], 16))
                else:
                    return chr(int(m.group(2)))
            except ValueError:
                return "&#%s;" % m.group(2)
        # Use Python's html.entities
        return html.entities.name2codepoint.get(m.group(2), f"&{m.group(2)};")
    return _UNESCAPE_RE.sub(convert_entity, ensure_str(value).strip())


def checkGZIP(url):
    from io import BytesIO
    import gzip
    from urllib.request import urlopen, Request
    hdr = {"User-Agent": "Enigma2 - Plugin"}
    req = Request(url, headers=hdr)
    try:
        response = urlopen(req, timeout=10)
        if response.info().get('Content-Encoding') == 'gzip':
            buffer = BytesIO(response.read())
            deflatedContent = gzip.GzipFile(fileobj=buffer)
            return deflatedContent.read().decode('utf-8')
        else:
            return response.read().decode('utf-8')
    except Exception as e:
        print(e)
        return None


def ssl_urlopen(url):
    context = ssl._create_unverified_context()
    from urllib.request import urlopen
    return urlopen(url, context=context)


class AspectManager:
    def __init__(self):
        try:
            self.init_aspect = self.get_current_aspect()
            print("[INFO] Initial aspect ratio:", self.init_aspect)
        except Exception as e:
            print("[ERROR] Failed to initialize aspect manager:", str(e))
            self.init_aspect = 0

    def get_current_aspect(self):
        try:
            aspect = AVSwitch().getAspectRatioSetting()
            return int(aspect) if aspect is not None else 0
        except Exception:
            return 0

    def set_aspect(self, aspect_ratio):
        aspect_map = {"4:3": 0, "16:9": 1, "16:10": 2, "auto": 3}
        if aspect_ratio in aspect_map:
            new_aspect = aspect_map[aspect_ratio]
            AVSwitch().setAspectRatio(new_aspect)
            return True
        return False

    def restore_aspect(self):
        if hasattr(self, 'init_aspect') and self.init_aspect is not None:
            AVSwitch().setAspectRatio(self.init_aspect)


aspect_manager = AspectManager()


def getDesktopSize():
    s = getDesktop(0).size()
    return (s.width(), s.height())


def isWQHD():
    w, h = getDesktopSize()
    return w == 2560 and h == 1440


def isUHD():
    w, h = getDesktopSize()
    return w == 3840 and h == 2160


def isFHD():
    w, h = getDesktopSize()
    return w == 1920 and h == 1080


def isHD():
    w, h = getDesktopSize()
    return w == 1280 and h == 720


def DreamOS():
    return exists('/var/lib/dpkg/status')


def mountipkpth():
    try:
        from Tools.Directories import fileExists
        mdevices = []
        if fileExists('/proc/mounts'):
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    if '/media/usb' in line:
                        p = '/media/usb/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/media/usb1' in line:
                        p = '/media/usb1/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/media/hdd' in line:
                        p = '/media/hdd/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/media/hdd2' in line:
                        p = '/media/hdd2/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/media/sdcard' in line:
                        p = '/media/sdcard/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/media/sd' in line:
                        p = '/media/sd/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/universe' in line:
                        p = '/universe/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/media/ba' in line:
                        p = '/media/ba/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
                    elif '/data' in line:
                        p = '/data/picon'
                        if not exists(p):
                            system(f'mkdir -p {p}')
                        mdevices.append(p)
        mdevices.append('/picon')
        mdevices.append('/usr/share/enigma2/picon')
        return mdevices
    except Exception as e:
        print(e)
        return []


def getEnigmaVersionString():
    try:
        from enigma import getEnigmaVersionString
        return getEnigmaVersionString()
    except Exception:
        return "N/A"


def getImageVersionString():
    try:
        from Tools.Directories import resolveFilename, SCOPE_SYSETC
        with open(resolveFilename(SCOPE_SYSETC, 'image-version'), 'r') as f:
            lines = f.readlines()
        for x in lines:
            splitted = x.split('=')
            if splitted[0] == "version":
                version = splitted[1]
                image_type = version[0]
                major = version[1]
                minor = version[2]
                revision = version[3]
                year = version[4:8]
                month = version[8:10]
                day = version[10:12]
                date = '-'.join((year, month, day))
                image_type_str = "Release" if image_type == '0' else "Experimental"
                version_str = '.'.join((major, minor, revision))
                if version_str != '0.0.0':
                    return ' '.join((image_type_str, version_str, date))
                else:
                    return ' '.join((image_type_str, date))
    except IOError:
        pass
    return "unavailable"


def mySkin():
    currentSkin = config.skin.primary_skin.value.replace('/skin.xml', '')
    return currentSkin


def getFreeMemory():
    mem_free = None
    mem_total = None
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemFree' in line:
                    parts = line.strip().split()
                    mem_free = float(parts[1])
                elif 'MemTotal' in line:
                    parts = line.strip().split()
                    mem_total = float(parts[1])
    except Exception:
        pass
    return (mem_free, mem_total)


def sizeToString(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes <= 0:
        return "0 B"
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.').replace(".", ",")
    return f'{f} {suffixes[i]}'


def convert_size(size_bytes):
    import math
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def getMountPoint(path):
    pathname = realpath(path)
    parent_device = stat(pathname).st_dev
    path_device = stat(pathname).st_dev
    mount_point = ""
    while parent_device == path_device:
        mount_point = pathname
        pathname = dirname(pathname)
        if pathname == mount_point:
            break
        parent_device = stat(pathname).st_dev
    return mount_point


def getMointedDevice(pathname):
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                fields = line.rstrip('\n').split()
                if fields[1] == pathname:
                    return fields[0]
    except Exception:
        pass
    return None


def getFreeSpace(path):
    try:
        mount_point = getMountPoint(path)
        device = getMointedDevice(mount_point)
        print(mount_point + "|" + device)
        st = statvfs(device)
        return sizeToString(st.f_bfree * st.f_bsize)
    except Exception:
        return "N/A"


def listDir(what):
    try:
        return listdir(what)
    except Exception:
        return None


def purge(directory, pattern):
    import re
    for f in listDir(directory) or []:
        file_path = join(directory, f)
        if isfile(file_path) and re.search(pattern, f):
            remove(file_path)


def getLanguage():
    try:
        language = config.osd.language.value
        return language[:-3]
    except Exception:
        return 'en'


def downloadFile(url, target):
    import socket
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError
    try:
        response = urlopen(url, None, 15)
        with open(target, 'wb') as output:
            output.write(response.read())
        response.close()
        return True
    except (HTTPError, URLError, socket.timeout):
        return False


def defaultMoviePath():
    result = config.usage.default_path.value
    if not isdir(result):
        from Tools import Directories
        return Directories.defaultRecordingLocation(
            config.usage.default_path.value)
    return result


if not isdir(config.movielist.last_videodir.value):
    try:
        config.movielist.last_videodir.value = defaultMoviePath()
        config.movielist.last_videodir.save()
    except Exception:
        pass
downloadm3u = config.movielist.last_videodir.value


def getserviceinfo(service_ref):
    try:
        from ServiceReference import ServiceReference
        ref = ServiceReference(service_ref)
        return ref.getServiceName(), ref.getPath()
    except Exception:
        return None, None


def sortedDictKeys(adict):
    return sorted(adict.keys())


def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield end_date - datetime.timedelta(n)


CountConnOk = 0


def zCheckInternet(opt=1, server=None, port=None):
    global CountConnOk
    checklist = [("8.8.4.4", 53), ("8.8.8.8", 53), ("www.lululla.altervista.org/",
                                                    80), ("www.linuxsat-support.com", 443), ("www.google.com", 443)]
    if opt < 5:
        srv = checklist[opt]
    else:
        srv = (server, port)
    try:
        import socket
        socket.setdefaulttimeout(0.5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(srv)
        CountConnOk = 0
        print(f'Status Internet: {srv[0]}:{srv[1]} -> OK')
        return True
    except Exception:
        print(f'Status Internet: {srv[0]}:{srv[1]} -> KO')
        if CountConnOk == 0 and opt not in (2, 3):
            CountConnOk = 1
            return zCheckInternet(0)
        elif CountConnOk == 1 and opt not in (2, 3):
            CountConnOk = 2
            return zCheckInternet(4)
        return False


def checkInternet():
    try:
        import socket
        socket.setdefaulttimeout(0.5)
        socket.socket(
            socket.AF_INET, socket.SOCK_STREAM).connect(
            ('8.8.8.8', 53))
        return True
    except Exception:
        return False


def check(url):
    from urllib.request import urlopen
    try:
        response = urlopen(url, None, 15)
        response.close()
        return True
    except Exception:
        return False


def testWebConnection(host='www.google.com', port=80, timeout=3):
    import socket
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as e:
        print('error: ', e)
        return False


def checkStr(text, encoding='utf8'):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text


def str_encode(text, encoding="utf8"):
    return str(text)


def checkRedirect(url):
    import requests
    from requests.adapters import HTTPAdapter
    hdr = {"User-Agent": "Enigma2 - Enigma2 Plugin"}
    http = requests.Session()
    http.mount("http://", HTTPAdapter())
    http.mount("https://", HTTPAdapter())
    try:
        x = http.get(url, headers=hdr, timeout=15, verify=False, stream=True)
        return str(x.url)
    except Exception as e:
        print(e)
        return str(url)


def freespace():
    try:
        diskSpace = statvfs('/')
        capacity = float(diskSpace.f_bsize * diskSpace.f_blocks)
        available = float(diskSpace.f_bsize * diskSpace.f_bavail)
        fspace = round(available / 1048576.0, 2)
        tspace = round(capacity / 1048576.0, 1)
        return f'Free space({fspace}MB) Total space({tspace}MB)'
    except Exception:
        return ''


def b64encoder(source):
    if isinstance(source, str):
        source = source.encode('utf-8')
    return base64.b64encode(source).decode('utf-8')


def b64decoder(data):
    data = data.strip()
    pad = len(data) % 4
    if pad == 1:
        return ""
    if pad:
        data += "=" * (4 - pad)
    try:
        decoded = base64.b64decode(data)
        return decoded.decode('utf-8')
    except Exception as e:
        print("Base64 decoding error: %s" % e)
        return ""


def __createdir(list):
    from os import mkdir
    dir = ''
    for line in list[1:].split('/'):
        dir += '/' + line
        if not exists(dir):
            try:
                mkdir(dir)
            except Exception:
                print('Mkdir Failed', dir)


def substr(data, start, end):
    i1 = data.find(start)
    i2 = data.find(end, i1)
    return data[i1:i2]


def uniq(inlist):
    return list(dict.fromkeys(inlist))


def ReloadBouquets():
    from enigma import eDVBDB
    db = eDVBDB.getInstance()
    db.reloadServicelist()
    db.reloadBouquets()


def deletetmp():
    system('rm -rf /tmp/unzipped;rm -f /tmp/*.ipk;rm -f /tmp/*.tar;rm -f /tmp/*.zip;rm -f /tmp/*.tar.gz;rm -f /tmp/*.tar.bz2;rm -f /tmp/*.tar.tbz2;rm -f /tmp/*.tar.tbz;rm -f /tmp/*.m3u')


def del_jpg():
    import glob
    for i in glob.glob(join('/tmp', '*.jpg')):
        try:
            chmod(i, 0o777)
            remove(i)
        except OSError:
            pass


def OnclearMem():
    try:
        system('sync')
        system('echo 1 > /proc/sys/vm/drop_caches')
        system('echo 2 > /proc/sys/vm/drop_caches')
        system('echo 3 > /proc/sys/vm/drop_caches')
    except Exception:
        pass


def MemClean():
    try:
        system('sync')
        for i in range(1, 4):
            system(f"echo {i} > /proc/sys/vm/drop_caches")
    except Exception:
        pass


def findSoftCamKey():
    paths = ['/usr/keys',
             '/etc/tuxbox/config/oscam-emu',
             '/etc/tuxbox/config/oscam-trunk',
             '/etc/tuxbox/config/oscam',
             '/etc/tuxbox/config/ncam',
             '/etc/tuxbox/config/gcam',
             '/etc/tuxbox/config',
             '/etc',
             '/var/keys']
    if exists('/tmp/.oscam/oscam.version'):
        with open('/tmp/.oscam/oscam.version', 'r') as f:
            data = f.readlines()
    elif exists('/tmp/.ncam/ncam.version'):
        with open('/tmp/.ncam/ncam.version', 'r') as f:
            data = f.readlines()
    elif exists('/tmp/.gcam/gcam.version'):
        with open('/tmp/.gcam/gcam.version', 'r') as f:
            data = f.readlines()
        for line in data:
            if 'configdir:' in line.lower():
                paths.insert(0, line.split(':')[1].strip())
    for path in paths:
        softcamkey = join(path, 'SoftCam.Key')
        if exists(softcamkey):
            return softcamkey
    return '/usr/keys/SoftCam.Key'


def web_info(message):
    try:
        from urllib.parse import quote_plus
        message = quote_plus(message)
        cmd = f"wget -qO - 'http://127.0.0.1/web/message?type=2&timeout=10&text={message}' > /dev/null 2>&1 &"
        popen(cmd)
    except Exception as e:
        print('web_info ERROR', e)


def trace_error():
    import traceback
    try:
        traceback.print_exc(file=sys.stdout)
        traceback.print_exc(file=open('/tmp/Error.log', 'a'))
    except Exception as e:
        print('trace_error:', e)


def log(label, data):
    with open('/tmp/my__debug.log', 'a') as f:
        f.write(f'\n{label}:>{str(data)}')


def ConverDate(data):
    year = data[:2]
    month = data[-4:][:2]
    day = data[-2:]
    return f"{day}-{month}-20{year}"


def ConverDateBack(data):
    year = data[-2:]
    month = data[-7:][:2]
    day = data[:2]
    return year + month + day


def isPythonFolder():
    path = "/usr/lib/"
    for name in listdir(path):
        fullname = join(path, name)
        if not isfile(fullname) and "python" in name:
            x = join(fullname, "site-packages", "streamlink")
            if exists(x):
                return x
    return False


def is_streamlink_available():
    return isPythonFolder()


def is_exteplayer3_Available():
    from enigma import eEnv
    path = eEnv.resolve("$bindir/exteplayer3")
    return isfile(path)


def AdultUrl(url):
    from urllib.request import urlopen, Request
    req = Request(url)
    req.add_header(
        'User-Agent',
        'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')
    r = urlopen(req, None, 15)
    link = r.read()
    r.close()
    if isinstance(link, bytes):
        link = link.decode("utf-8", errors='ignore')
    return link


# Lista degli User-Agent (accorciata per esempio, ma tenerla completa
# dall'originale)
ListAgent = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.15 (KHTML, like Gecko) Chrome/24.0.1295.0 Safari/537.15',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.14 (KHTML, like Gecko) Chrome/24.0.1292.0 Safari/537.14',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
    'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1284.0 Safari/537.13',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8',
    'Mozilla/6.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
    'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20120427 Firefox/15.0a1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20120427 Firefox/15.0a1',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:15.0) Gecko/20120910144328 Firefox/15.0.2',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:9.0a2) Gecko/20111101 Firefox/9.0a2',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110613 Firefox/6.0a2',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110612 Firefox/6.0a2',
    'Mozilla/5.0 (Windows NT 6.1; rv:6.0) Gecko/20110814 Firefox/6.0',
    'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)',
    'Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
    'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0;  it-IT)',
    'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US)'
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/13.0.782.215)',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/11.0.696.57)',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0) chromeframe/10.0.648.205',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.1; SV1; .NET CLR 2.8.52393; WOW64; en-US)',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/4.0; GTB7.4; InfoPath.3; SV1; .NET CLR 3.1.76908; WOW64; en-US)',
    'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.2; SV1; .NET CLR 3.3.69573; WOW64; en-US)',
    'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)',
    'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; InfoPath.1; SV1; .NET CLR 3.8.36217; WOW64; en-US)',
    'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; it-IT)',
    'Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)',
    'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16.2',
    'Opera/12.80 (Windows NT 5.1; U; en) Presto/2.10.289 Version/12.02',
    'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00',
    'Opera/9.80 (Windows NT 5.1; U; zh-sg) Presto/2.9.181 Version/12.00',
    'Opera/12.0(Windows NT 5.2;U;en)Presto/22.9.168 Version/12.00',
    'Opera/12.0(Windows NT 5.1;U;en)Presto/22.9.168 Version/12.00',
    'Mozilla/5.0 (Windows NT 5.1) Gecko/20100101 Firefox/14.0 Opera/12.0',
    'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10',
    'Mozilla/5.0 (iPad; CPU OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko ) Version/5.1 Mobile/9B176 Safari/7534.48.3']


def RequestAgent():
    return choice(ListAgent)


def make_request(url):
    try:
        import requests
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            return response.text
    except ImportError:
        from urllib.request import urlopen, Request
        req = Request(url)
        req.add_header('User-Agent', 'E2 Plugin')
        response = urlopen(req, None, 10)
        link = response.read().decode('utf-8')
        response.close()
        return link
    return None


def ReadUrl(url):
    from urllib.request import urlopen, Request
    try:
        CONTEXT = ssl._create_unverified_context()
    except Exception:
        CONTEXT = None
    print('ReadUrl1:\n  url = %s' % url)
    try:
        req = Request(url)
        req.add_header('User-Agent', RequestAgent())
        try:
            r = urlopen(req, None, 30, context=CONTEXT)
        except Exception:
            r = urlopen(req, None, 30)
        link = r.read()
        r.close()
        if isinstance(link, bytes):
            for enc in ('utf-8', 'cp437', 'iso-8859-1'):
                try:
                    link = link.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
        return link
    except Exception as e:
        print('ReadUrl5 - Error: ', e)
        return None


def ReadUrl2(url, referer):
    from urllib.request import urlopen, Request
    try:
        CONTEXT = ssl._create_unverified_context()
    except Exception:
        CONTEXT = None
    req = Request(url)
    req.add_header('User-Agent', RequestAgent())
    req.add_header('Referer', referer)
    try:
        r = urlopen(req, None, 30, context=CONTEXT)
    except Exception:
        r = urlopen(req, None, 30)
    link = r.read()
    r.close()
    if isinstance(link, bytes):
        for enc in ('utf-8', 'cp437', 'iso-8859-1'):
            try:
                link = link.decode(enc)
                break
            except UnicodeDecodeError:
                continue
    return link


def getUrlSiVer(url, verify=True):
    try:
        headers = {'User-Agent': RequestAgent()}
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            verify=verify)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print("Error fetching URL " + str(url) + ": " + str(e))
        return None


def getUrlNoVer(url, verify=True):
    try:
        headers = {'User-Agent': RequestAgent()}
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            verify=verify)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching URL {url}: {str(e)}")
        return None


def getUrl(url):
    from urllib.request import urlopen, Request
    import ssl
    req = Request(url, headers={'User-Agent': RequestAgent()})
    context = ssl._create_unverified_context()
    response = urlopen(req, timeout=30, context=context)
    # final_url = response.geturl()  # eventuale redirect
    content = response.read().decode('utf-8', errors='ignore')
    response.close()
    return content


def getUrl2(url, referer):
    from urllib.request import urlopen, Request
    req = Request(url)
    req.add_header('User-Agent', RequestAgent())
    req.add_header('Referer', referer)
    try:
        response = urlopen(req, timeout=10)
        link = response.read().decode()
        response.close()
        return link
    except Exception:
        context = ssl._create_unverified_context()
        response = urlopen(req, timeout=10, context=context)
        link = response.read().decode()
        response.close()
        return link


def getUrlresp(url):
    from urllib.request import urlopen, Request
    req = Request(url)
    req.add_header('User-Agent', RequestAgent())
    try:
        return urlopen(req, timeout=10)
    except Exception:
        context = ssl._create_unverified_context()
        return urlopen(req, timeout=10, context=context)


def decodeUrl(text):
    replacements = {
        '%20': ' ', '%21': '!', '%22': '"', '%23': '&', '%24': '$',
        '%25': '%', '%26': '&', '%2B': '+', '%2F': '/', '%3A': ':',
        '%3B': ';', '%3D': '=', '&#x3D;': '=', '%3F': '?', '%40': '@'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def normalize(title):
    try:
        if isinstance(title, bytes):
            title = title.decode('utf-8')
        return ''.join(c for c in unicodedata.normalize(
            'NFKD', title) if unicodedata.category(c) != 'Mn')
    except Exception:
        return str(title)


def get_safe_filename(filename, fallback=''):
    import re
    name = filename.replace(' ', '_').replace('/', '_')
    name = unicodedata.normalize(
        'NFKD', str(name)).encode(
        'ASCII', 'ignore').decode('ASCII')
    name = re.sub(r'[^a-z0-9-_]', '', name.lower())
    if not name:
        name = fallback
    return name


def decodeHtml(text):
    import html
    text = html.unescape(text)
    replacements = {
        '&amp;': '&', '&apos;': "'", '&lt;': '<', '&gt;': '>', '&ndash;': '-',
        '&quot;': '"', '&ntilde;': '~', '&rsquo;': "'", '&nbsp;': ' ',
        '&equals;': '=', '&quest;': '?', '&comma;': ',', '&period;': '.',
        '&colon;': ':', '&lpar;': '(', '&rpar;': ')', '&excl;': '!',
        '&dollar;': '$', '&num;': '#', '&ast;': '*', '&lowbar;': '_',
        '&lsqb;': '[', '&rsqb;': ']', '&half;': '1/2', '&DiacriticalTilde;': '~',
        '&OpenCurlyDoubleQuote;': '"', '&CloseCurlyDoubleQuote;': '"'
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    return text.strip()


conversion = {
    'а': 'a', 'А': 'A', 'б': 'b', 'Б': 'B', 'в': 'v', 'В': 'V',
    'г': 'g', 'Г': 'G', 'д': 'd', 'Д': 'D', 'е': 'e', 'Е': 'E',
    'ё': 'jo', 'Ё': 'jo', 'ж': 'zh', 'Ж': 'ZH', 'з': 'z', 'З': 'Z',
    'и': 'i', 'И': 'I', 'й': 'j', 'Й': 'J', 'к': 'k', 'К': 'K',
    'л': 'l', 'Л': 'L', 'м': 'm', 'М': 'M', 'н': 'n', 'Н': 'N',
    'о': 'o', 'О': 'O', 'п': 'p', 'П': 'P', 'р': 'r', 'Р': 'R',
    'с': 's', 'С': 'S', 'т': 't', 'Т': 'T', 'у': 'u', 'У': 'U',
    'ф': 'f', 'Ф': 'F', 'х': 'h', 'Х': 'H', 'ц': 'c', 'Ц': 'C',
    'ч': 'ch', 'Ч': 'CH', 'ш': 'sh', 'Ш': 'SH', 'щ': 'sh', 'Щ': 'SH',
    'ъ': '', 'Ъ': '', 'ы': 'y', 'Ы': 'Y', 'ь': 'j', 'Ь': 'J',
    'э': 'je', 'Э': 'JE', 'ю': 'ju', 'Ю': 'JU', 'я': 'ja', 'Я': 'JA'
}


def cyr2lat(text):
    return ''.join(conversion.get(ch, ch) for ch in text)


def charRemove(text):
    char = [
        '1080p',
        'PF1',
        'PF2',
        'PF3',
        'PF4',
        'PF5',
        'PF6',
        'PF7',
        'PF8',
        'PF9',
        'PF10',
        'PF11',
        'PF12',
        'PF13',
        'PF14',
        'PF15',
        'PF16',
        'PF17',
        'PF18',
        'PF19',
        'PF20',
        'PF21',
        'PF22',
        'PF23',
        'PF24',
        'PF25',
        'PF26',
        'PF27',
        'PF28',
        'PF29',
        'PF30',
        '480p',
        '4K',
        '720p',
        'ANIMAZIONE',
        'BIOGRAFICO',
        'BDRip',
        'BluRay',
        'CINEMA',
        'DOCUMENTARIO',
        'DRAMMATICO',
        'FANTASCIENZA',
        'FANTASY',
        'HDCAM',
        'HDTC',
        'HDTS',
        'LD',
        'MAFIA',
        'MARVEL',
        'MD',
        'NEW_AUDIO',
        'POLIZIE',
        'R3',
        'R6',
        'SD',
        'SENTIMENTALE',
        'TC',
        'TEEN',
        'TELECINE',
        'TELESYNC',
        'THRILLER',
        'Uncensored',
        'V2',
        'WEBDL',
        'WEBRip',
        'WEB',
        'WESTERN',
        '-',
        '_',
        '.',
        '+',
        '[',
        ']',
        # 'APR',
        # 'AVVENTURA',
        # 'COMMEDIA',
        # 'FEB',
        # 'GEN',
        # 'GIU',
        # 'MAG',
        # 'ORROR',
    ]
    myreplace = text
    for ch in char:
        myreplace = myreplace.replace(
            ch,
            '').replace(
            '  ',
            ' ').replace(
            '   ',
            ' ').strip()
    return myreplace


def clean_html(html):
    import xml.sax.saxutils as saxutils
    if isinstance(html, bytes):
        html = html.decode('utf-8', 'ignore')
    html = html.replace('\n', ' ')
    html = re.sub(r'\s*<\s*br\s*/?\s*>\s*', '\n', html)
    html = re.sub(r'<\s*/\s*p\s*>\s*<\s*p[^>]*>', '\n', html)
    html = re.sub('<.*?>', '', html)
    html = saxutils.unescape(html)
    return html.strip()


def cachedel(folder):
    system(f"rm {folder}/*")


def cleanName(name):
    non_allowed = "/.\\:*?<>|\""
    try:
        if not isinstance(name, str):
            name = str(name)
        name = unicodedata.normalize(
            "NFKD", name).encode(
            "ASCII", "ignore").decode("ASCII")
        name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
        name = name.replace(' ', '-').replace("'", '').replace('&', 'e')
        name = name.replace('(', '').replace(')', '')
        name = name.strip()
        name = ''.join(['_' if c in non_allowed or ord(c)
                       < 32 else c for c in name])
    except Exception as e:
        print("Error in cleanName: " + str(e))
        name = "noname"
    return name


def cleantitle(title):
    import re
    clean = re.sub(r'[\'\<\>\:\"\/\\\|\?\*\(\)\[\]]', "", str(title))
    clean = re.sub(r"   ", " ", clean)
    clean = re.sub(r"  ", " ", clean)
    clean = re.sub(r" ", "-", clean)
    clean = re.sub(r"---", "-", clean)
    return clean.strip()


def cleanTitle(x):
    for ch in '~#%&*{}:<>?/+"|\\':
        x = x.replace(ch, '')
    x = x.replace('--', '-')
    return x


def remove_line(filename, pattern):
    if not isfile(filename):
        return
    with open(filename, 'r') as f:
        lines = [line for line in f if pattern not in line]
    with open(filename, 'w') as f:
        f.writelines(lines)


def badcar(name):
    bad = [
        "sd",
        "hd",
        "fhd",
        "uhd",
        "4k",
        "1080p",
        "720p",
        "blueray",
        "x264",
        "aac",
        "ozlem",
        "hindi",
        "hdrip",
        "(cache)",
        "(kids)",
        "[3d-en]",
        "[iran-dubbed]",
        "imdb",
        "top250",
        "multi-audio",
        "multi-subs",
        "multi-sub",
        "[audio-pt]",
        "[nordic-subbed]",
        "[nordic-subbeb]",
        "SD",
        "HD",
        "FHD",
        "UHD",
        "4K",
        "1080P",
        "720P",
        "BLUERAY",
        "X264",
        "AAC",
        "OZLEM",
        "HINDI",
        "HDRIP",
        "(CACHE)",
        "(KIDS)",
        "[3D-EN]",
        "[IRAN-DUBBED]",
        "IMDB",
        "TOP250",
        "MULTI-AUDIO",
        "MULTI-SUBS",
        "MULTI-SUB",
        "[AUDIO-PT]",
        "[NORDIC-SUBBED]",
        "[NORDIC-SUBBEB]",
        "-ae-",
        "-al-",
        "-ar-",
        "-at-",
        "-ba-",
        "-be-",
        "-bg-",
        "-br-",
        "-cg-",
        "-ch-",
        "-cz-",
        "-da-",
        "-de-",
        "-dk-",
        "-ee-",
        "-en-",
        "-es-",
        "-ex-yu-",
        "-fi-",
        "-fr-",
        "-gr-",
        "-hr-",
        "-hu-",
        "-in-",
        "-ir-",
        "-it-",
        "-lt-",
        "-mk-",
        "-mx-",
        "-nl-",
        "-no-",
        "-pl-",
        "-pt-",
        "-ro-",
        "-rs-",
        "-ru-",
        "-se-",
        "-si-",
        "-sk-",
        "-tr-",
        "-uk-",
        "-us-",
        "-yu-",
        "-AE-",
        "-AL-",
        "-AR-",
        "-AT-",
        "-BA-",
        "-BE-",
        "-BG-",
        "-BR-",
        "-CG-",
        "-CH-",
        "-CZ-",
        "-DA-",
        "-DE-",
        "-DK-",
        "-EE-",
        "-EN-",
        "-ES-",
        "-EX-YU-",
        "-FI-",
        "-FR-",
        "-GR-",
        "-HR-",
        "-HU-",
        "-IN-",
        "-IR-",
        "-IT-",
        "-LT-",
        "-MK-",
        "-MX-",
        "-NL-",
        "-NO-",
        "-PL-",
        "-PT-",
        "-RO-",
        "-RS-",
        "-RU-",
        "-SE-",
        "-SI-",
        "-SK-",
        "-TR-",
        "-UK-",
        "-US-",
        "-YU-",
        "|ae|",
        "|al|",
        "|ar|",
        "|at|",
        "|ba|",
        "|be|",
        "|bg|",
        "|br|",
        "|cg|",
        "|ch|",
        "|cz|",
        "|da|",
        "|de|",
        "|dk|",
        "|ee|",
        "|en|",
        "|es|",
        "|ex-yu|",
        "|fi|",
        "|fr|",
        "|gr|",
        "|hr|",
        "|hu|",
        "|in|",
        "|ir|",
        "|it|",
        "|lt|",
        "|mk|",
        "|mx|",
        "|nl|",
        "|no|",
        "|pl|",
        "|pt|",
        "|ro|",
        "|rs|",
        "|ru|",
        "|se|",
        "|si|",
        "|sk|",
        "|tr|",
        "|uk|",
        "|us|",
        "|yu|",
        "|AE|",
        "|AL|",
        "|AR|",
        "|AT|",
        "|BA|",
        "|BE|",
        "|BG|",
        "|BR|",
        "|CG|",
        "|CH|",
        "|CZ|",
        "|DA|",
        "|DE|",
        "|DK|",
        "|EE|",
        "|EN|",
        "|ES|",
        "|EX-YU|",
        "|FI|",
        "|FR|",
        "|GR|",
        "|HR|",
        "|HU|",
        "|IN|",
        "|IR|",
        "|IT|",
        "|LT|",
        "|MK|",
        "|MX|",
        "|NL|",
        "|NO|",
        "|PL|",
        "|PT|",
        "|RO|",
        "|RS|",
        "|RU|",
        "|SE|",
        "|SI|",
        "|SK|",
        "|TR|",
        "|UK|",
        "|US|",
        "|YU|",
        "|Ae|",
        "|Al|",
        "|Ar|",
        "|At|",
        "|Ba|",
        "|Be|",
        "|Bg|",
        "|Br|",
        "|Cg|",
        "|Ch|",
        "|Cz|",
        "|Da|",
        "|De|",
        "|Dk|",
        "|Ee|",
        "|En|",
        "|Es|",
        "|Ex-Yu|",
        "|Fi|",
        "|Fr|",
        "|Gr|",
        "|Hr|",
        "|Hu|",
        "|In|",
        "|Ir|",
        "|It|",
        "|Lt|",
        "|Mk|",
        "|Mx|",
        "|Nl|",
        "|No|",
        "|Pl|",
        "|Pt|",
        "|Ro|",
        "|Rs|",
        "|Ru|",
        "|Se|",
        "|Si|",
        "|Sk|",
        "|Tr|",
        "|Uk|",
        "|Us|",
        "|Yu|",
        "(",
        ")",
        "[",
        "]",
        "u-",
        "3d",
        "'",
        "#",
        "/",
        "-",
        "_",
        ".",
        "+",
        "PF1",
        "PF2",
        "PF3",
        "PF4",
        "PF5",
        "PF6",
        "PF7",
        "PF8",
        "PF9",
        "PF10",
        "PF11",
        "PF12",
        "PF13",
        "PF14",
        "PF15",
        "PF16",
        "PF17",
        "PF18",
        "PF19",
        "PF20",
        "PF21",
        "PF22",
        "PF23",
        "PF24",
        "PF25",
        "PF26",
        "PF27",
        "PF28",
        "PF29",
        "PF30",
        "480p",
        "ANIMAZIONE",
        "AVVENTURA",
        "BIOGRAFICO",
        "BDRip",
        "BluRay",
        "CINEMA",
        "COMMEDIA",
        "DOCUMENTARIO",
        "DRAMMATICO",
        "FANTASCIENZA",
        "FANTASY",
        "HDCAM",
        "HDTC",
        "HDTS",
        "LD",
        "MARVEL",
        "MD",
        "NEW_AUDIO",
        "R3",
        "R6",
        "SENTIMENTALE",
        "TC",
        "TELECINE",
        "TELESYNC",
        "THRILLER",
        "Uncensored",
        "V2",
        "WEBDL",
        "WEBRip",
        "WEB",
        "WESTERN"]
    for i in range(1900, 2025):
        bad.append(str(i))
    for b in bad:
        name = name.replace(b, '')
    return name


def get_title(title):
    if title is None:
        return
    title = re.sub(r'&#(\d+);', '', title)
    title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '"').replace('&amp;', '&')
    title = re.sub(
        r'\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\s',
        '',
        title).lower()
    return title


def clean_filename(s):
    if not s:
        return ''
    for c in '\\/:*?"<>|\'':
        s = s.replace(c, '')
    return s.strip()


def cleantext(text):
    import html
    text = html.unescape(text)
    replacements = {
        '&amp;': '&', '&apos;': "'", '&lt;': '<', '&gt;': '>', '&ndash;': '-',
        '&quot;': '"', '&ntilde;': '~', '&rsquo;': "'", '&nbsp;': ' ',
        '&equals;': '=', '&quest;': '?', '&comma;': ',', '&period;': '.',
        '&colon;': ':', '&lpar;': '(', '&rpar;': ')', '&excl;': '!',
        '&dollar;': '$', '&num;': '#', '&ast;': '*', '&lowbar;': '_',
        '&lsqb;': '[', '&rsqb;': ']', '&half;': '1/2', '&DiacriticalTilde;': '~',
        '&OpenCurlyDoubleQuote;': '"', '&CloseCurlyDoubleQuote;': '"'
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    return text.strip()


def cleanhtml(raw_html):
    return re.sub('<.*?>', '', raw_html)


def addstreamboq(bouquetname=None):
    boqfile = '/etc/enigma2/bouquets.tv'
    if not exists(boqfile):
        return
    with open(boqfile, 'r') as fp:
        lines = fp.readlines()
    add = True
    for line in lines:
        if f'userbouquet.{bouquetname}.tv' in line:
            add = False
            break
    if add:
        with open(boqfile, 'a') as fp:
            fp.write(
                f'#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.{bouquetname}.tv" ORDER BY bouquet\n')


def stream2bouquet(url=None, name=None, bouquetname=None):
    from urllib.parse import quote
    bouquetname = 'MyFavoriteBouquet'
    fileName = f'/etc/enigma2/userbouquet.{bouquetname}.tv'
    out = f'#SERVICE 4097:0:0:0:0:0:0:0:0:0:{quote(url)}:{quote(name)}\r\n'
    try:
        addstreamboq(bouquetname)
        if not exists(fileName):
            with open(fileName, 'w') as fp:
                fp.write(f'#NAME {bouquetname}\n')
            with open(fileName, 'a') as fp:
                fp.write(out)
        else:
            with open(fileName, 'r') as fp:
                lines = fp.readlines()
            for line in lines:
                if out in line:
                    return 'Stream already added to bouquet'
            with open(fileName, 'a') as fp:
                fp.write(out)
    except Exception:
        return 'Adding to bouquet failed'
    return None
