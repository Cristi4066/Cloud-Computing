import http.server
import socketserver
import http.client
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import mysql.connector
from mysql.connector import Error


def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
        resp = "succes"
    except Error as e:
        print(f"The error '{e}' occurred")
        resp = f"The error '{e}' occurred"

    return resp


def execute_read_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")
        return "Bad"


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):

        query_components = parse_qs(urlparse(self.path).query)
        if not query_components:

            data = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(data.decode())

        else:
            data = query_components

        select = "SELECT * FROM "
        select += str(data["table"][0])
        select += " WHERE "
        if "column" in data and "value" in data:
            if len(data["column"]) < len(data["values"]):
                self.send_response(400)
                self.send_header("Content-type", "JSON")
                self.end_headers()
                self.wfile.write(json.dumps("More values than columns").encode())
            for i in range(len(data["column"])):
                if i >= len(data["value"]):
                    self.send_response(400)
                    self.send_header("Content-type", "JSON")
                    self.end_headers()
                    self.wfile.write(json.dumps("Not enough values").encode())
                    return
                select += str(data["column"][i]) + " = '" + str(data["value"][i]) + "' AND "
        select = select[:len(select) - 5]
        select += ";"
        resp = execute_read_query(connection, select)

        if resp == "Bad":
            self.send_response(400)
            self.send_header("Content-type", "JSON")
            self.end_headers()
            self.wfile.write(json.dumps("Wrong syntax").encode())
        else:
            if not resp:
                self.send_response(204)
                self.send_header("Content-type", "JSON")
                self.end_headers()
                self.wfile.write(json.dumps("0 rows selected").encode())
            else:
                self.send_response(200)
                self.send_header("Content-type", "JSON")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode())
        return

    def do_POST(self):

        data = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(data.decode())

        insert = "INSERT INTO "
        insert += data["table"]
        insert += f" (nume, prenume, varsta) VALUES ('"
        if "values" in data:
            for dat in data["values"]:
                insert += str(dat) + "', '"

        insert = insert[:len(insert) - 3]
        insert += ");"

        err = execute_query(connection, insert)

        if err == "succes":

            self.send_response(201)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("Line corectly introduced").encode())

        else:

            self.send_response(400)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("Wrong data introduced").encode())

        return

    def do_PUT(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(data.decode())

        select = "SELECT * FROM "
        select += str(data["table"])
        select += " WHERE "
        if "column" in data and "value" in data:
            for i in range(len(data["column"])):
                select += str(data["column"][i]) + " = '" + str(data["value"][i]) + "' AND "
        select = select[:len(select) - 5]
        select += ";"
        resp = execute_read_query(connection, select)
        if not resp:
            self.send_response(404)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("The row does not exist").encode())
            return

        update = "UPDATE "
        update += data["table"]
        update += " SET "
        if "change_column" in data and "change_value" in data:
            for i in range(len(data["change_column"])):
                update += str(data["change_column"][i]) + " = '" + str(data["change_value"][i]) + "', "

        update = update[:len(update) - 2]
        update += " WHERE "

        if "column" in data and "value" in data:
            for i in range(len(data["column"])):
                update += str(data["column"][i]) + " = '" + str(data["value"][i]) + "' AND "

        update = update[:len(update) - 5]
        update += ";"

        print(update)

        err = execute_query(connection, update)

        if err == "succes":

            self.send_response(200)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("Row changed").encode())

        else:

            self.send_response(400)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("Syntax error").encode())


    def do_DELETE(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(data.decode())

        select = "SELECT * FROM "
        select += str(data["table"])
        select += " WHERE "
        if "column" in data and "value" in data:
            for i in range(len(data["column"])):
                select += str(data["column"][i]) + " = '" + str(data["value"][i]) + "' AND "
        select = select[:len(select) - 5]
        select += ";"
        resp = execute_read_query(connection, select)
        if not resp:
            self.send_response(404)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("The row does not exist").encode())
            return

        delete = "DELETE FROM "
        delete += data["table"]
        delete += " WHERE "
        if "column" in data and "value" in data:
            for i in range(len(data["column"])):
                if i >= len(data["value"]):
                    self.send_response(400)
                    self.send_header("Content-type", "JSON")
                    self.end_headers()
                    self.wfile.write(json.dumps("Wrong syntax").encode())
                    return
                delete += str(data["column"][i]) + " = " + str(data["value"][i]) + " AND "

        delete = delete[:len(delete) - 5]
        delete += ";"

        err = execute_query(connection, delete)

        if err == "succes":
            self.send_response(200)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("Table changed").encode())
        else:

            self.send_response(400)
            self.send_header("Content-type", "JSON")
            self.end_headers()

            self.wfile.write(json.dumps("Something went wrong").encode())


connection = create_connection("localhost", "root", "cristi", "student")

handler_object = MyHttpRequestHandler

PORT = 8000
my_server = socketserver.TCPServer(("", PORT), handler_object)

my_server.serve_forever()
