from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hglhasglkhsdlgh"
socketio = SocketIO(app, cors_allowed_origins="*")

# -----Logic for rooms------
rooms = {}

def generate_room_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code 

def create_room_from_code(code):
    rooms[code] = {"players": [], "host": ""}
    session["roomCode"] = code

# -----Routes------
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        codeInput = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if create != False:
            roomCode = generate_room_code(4)
            create_room_from_code(roomCode)
            return render_template("home.html", roomCode=roomCode, codeInput=roomCode)
        
        if join != False:
            if not name:
                return render_template("home.html", error="Please enter a name")
            if not codeInput:
                return render_template("home.html", error="Please enter a room code")
       
        if codeInput not in rooms:
            return render_template("home.html", error="Room does not exist")
        
        if not rooms[codeInput]["host"]:
            rooms[codeInput]["host"] = name

        session["name"] = name
        session["roomCode"] = codeInput


        rooms[codeInput]["players"].append({
            "name": name,
            "inLobby": True
        })

        return redirect(url_for("lobby"))

    return render_template("home.html")

@app.route("/lobby", methods=["POST", "GET"])
def lobby():
    roomCode = session.get("roomCode")
    
    if request.method == "POST":
        return redirect(url_for("inGame"))


    return render_template(
        "lobby.html", 
        players = [player["name"] + " (you)" if player["name"] == session["name"] else player["name"] for player in rooms[roomCode]["players"] if player["inLobby"]],
        code = roomCode
    )

@app.route("/inGame")
def inGame():
    return render_template(
        "inGame.html",
        code = session.get("roomCode")
    )
    

@socketio.on("connect")
def connect(auth):
    roomCode = session.get("roomCode")
    name = session.get("name")
    if not roomCode or not name:
        return
    if roomCode not in rooms:
        leave_room(roomCode)
        return
    
    join_room(roomCode)
    send({"name": name}, to=roomCode)
    print(f"{name} joined room {roomCode}")

# -----Chat------
@socketio.on('message')
def handle_message(message):
    print("Received message: " + message)
    if message != "User connected!":
        send(message, broadcast=True)

# -----Run------
if __name__ == "__main__":
    socketio.run(app, debug=True)