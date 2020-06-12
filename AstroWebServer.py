import threading
import http.server
import socketserver
import sys
import os
import json

queue = None
players = None


class ServerHttpRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        global routes
        if self.path == '/api':
            # api
            global queue

            launcher = queue.get()
            queue.put(launcher)

            self.send_response(200)

            self.send_header("Content-type", "text/json")
            self.end_headers()

            global players

            s = launcher.settings
            res = {
                "settings": {
                    "MaxServerFramerate": s["MaxServerFramerate"],
                    "PublicIP": s["PublicIP"],
                    "ServerName": s["ServerName"],
                    "MaximumPlayerCount": s["MaximumPlayerCount"],
                    "OwnerName": s["OwnerName"],
                    "OwnerGuid": s["OwnerGuid"],
                    "DenyUnlistedPlayers": s["DenyUnlistedPlayers"],
                    "VerbosePlayerProperties": s["VerbosePlayerProperties"],
                    "AutoSaveGameInterval": s["AutoSaveGameInterval"],
                    "BackupSaveGamesInterval": s["BackupSaveGamesInterval"],
                    "ServerGuid": s["ServerGuid"],
                    "ActiveSaveFileDescriptiveName": s["ActiveSaveFileDescriptiveName"],
                    "ServerAdvertisedName": s["ServerAdvertisedName"],
                    "Port": s["Port"]
                },
                "players": launcher.playerList
            }

            self.wfile.write(
                bytes(json.dumps(res, separators=(',', ':')), "utf8"))

        elif self.path in routes:
            # static files
            self.send_response(200)
            if routes[self.path]['type'] == "text":
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(routes[self.path]['content'])
            elif routes[self.path]['type'] == "image":
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.wfile.write(routes[self.path]['content'])

        else:
            # 404
            self.send_response(404)

            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(bytes(
                "<html><head><title>Not Found</title></head><body>Not Found</body></html>", 'utf8'))

        return
        # http.server.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, format, *args):
        return


# handler = http.server.SimpleHTTPRequestHandler
handler = ServerHttpRequestHandler


class AstroWebServer(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        # assign queue inside the thread
        global queue
        queue = self.queue

        # load content from files to be served
        global routes
        routes = {
            "/": {
                "path": "index.html",
                "type": "text"
            },
            "/script.js": {
                "path": "script.js",
                "type": "text"
            },
            "/style.css": {
                "path": "style.css",
                "type": "text"
            },
            "/astrolauncherlogo.ico": {
                "path": "astrolauncherlogo.ico",
                "type": "image"
            }
        }

        for key in routes:
            with open(os.path.join(sys._MEIPASS, routes[key]['path']), 'rb') as contentFile:
                routes[key]['content'] = contentFile.read()

        with socketserver.TCPServer(("", 80), handler) as httpd:
            httpd.serve_forever()


def startWebServer(exchangeQueue):
    try:
        server = AstroWebServer(exchangeQueue)
        server.daemon = True
        server.start()
    except Exception as e:
        print("ERROR: %s" % e)
