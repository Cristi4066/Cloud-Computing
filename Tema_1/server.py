import http.server
import socketserver
import http.client
import json
import time
from urllib.parse import urlparse
from urllib.parse import parse_qs


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        self.send_header("Content-type", "text/html")

        self.end_headers()

        f = open("text.txt", "a")

        start_time = time.time()

        name = 'Iasi'
        query_components = parse_qs(urlparse(self.path).query)
        if 'location' in query_components:
            name = query_components["location"][0]

        api_weather = "4ca72f2f022e4c45bec161344212502"
        api_geo = "afc5d41beecd4825b61a2fb52e300f8b"

        conn = http.client.HTTPSConnection("www.random.org")
        conn.request("GET", "/integers/?num=1&min=1&max=3&col=1&base=10&format=plain&rnd=new")
        nr_of_days = int(conn.getresponse().read().decode())

        time1 = time.time()

        f.write(f'Request: [GET] www.random.org/integers/?num=1&min=1&max=3&col=1&base=10&format=plain&rnd=new\n'
                f'Respond: {nr_of_days}\n'
                f'Latency: {time1 - start_time}\n')

        text = "<p>Number of days: " + str(nr_of_days) + "</p>"

        conn = http.client.HTTPSConnection("api.opencagedata.com")
        conn.request("GET", f'/geocode/v1/json?q={name}&key={api_geo}')
        data = conn.getresponse().read().decode()
        data = json.loads(data)

        lat, lng = data["results"][0]["bounds"]["northeast"]["lat"], data["results"][0]["bounds"]["northeast"]["lng"]
        time2 = time.time()
        f.write(f'Request: [GET] api.opencagedata.com/geocode/v1/json?q={name}&key={api_geo}\n'
                f'Respond: {lat}, {lng}\n'
                f'Latency: {time2 - time1}\n')

        text = text + "<p>Lat: " + str(lat) + ", Long: " + str(lng) + "</p>"

        conn = http.client.HTTPSConnection("api.weatherapi.com")
        conn.request("GET", f'/v1/forecast.json?key={api_weather}&q={lat},{lng}&days={nr_of_days}')
        data = conn.getresponse().read().decode()
        data = json.loads(data)
        lists = list()
        for i in range(nr_of_days):
            lists.append(data["forecast"]["forecastday"][i]["day"]["maxtemp_c"])
            text = text + "<p>Temperature: " + str(data["forecast"]["forecastday"][i]["day"]["maxtemp_c"]) + "</p>"
        end_time = time.time()
        f.write(f'Request: [GET] api.weatherapi.com/v1/forecast.json?key={api_weather}&q={lat},{lng}&days={nr_of_days}\n'
                f'Respond: {lists}\n'
                f'Latency: {end_time - time2}\n')

        latency = end_time - start_time
        text += f'<p>Latency: {latency}</p>'
        html = f"<html><head></head><body><h1>{text}</h1></body></html>"

        self.wfile.write(bytes(html, "utf8"))

        return


handler_object = MyHttpRequestHandler

PORT = 8000
my_server = socketserver.TCPServer(("", PORT), handler_object)

my_server.serve_forever()
