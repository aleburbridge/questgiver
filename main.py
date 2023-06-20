from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO, emit
import random
from string import ascii_uppercase
from roles import Role

app = Flask(__name__)
app.config["SECRET_KEY"] = "hglhasglkhsdlgh"
socketio = SocketIO(app)

rooms = {}
emojis = ["😏","🤠","👹","👽","🙊","👻","🤡","😼","👀","🦄","🐔","🐸"]

def generate_room_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code 

def create_room_from_code(code):
    rooms[code] = {"players": [], "host": "", "assignedEmojis": []}
    session["roomCode"] = code

# -----Routes below this line ------
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
        
        if join != False and not name:
            return render_template("home.html", error="Please enter a name")
        
        if join != False and not codeInput:
            return render_template("home.html", error="Please enter a room code")
       
        if codeInput not in rooms:
            return render_template("home.html", error="Room does not exist")
        
        if not rooms[codeInput]["host"]:
            rooms[codeInput]["host"] = name

        session["name"] = name
        session["roomCode"] = codeInput

        if "emoji" not in session:
            available_emojis = list(set(emojis) - set(rooms[codeInput]["assignedEmojis"]))
            if available_emojis:
                emoji = random.choice(available_emojis)
            else: 
                emoji = "👹"
            session["emoji"] = emoji
            rooms[codeInput]["assignedEmojis"].append(emoji)

        rooms[codeInput]["players"].append({
            "name": name,
            "emoji": session["emoji"],
            "inLobby": True
        })

        return redirect(url_for("lobby"))

    return render_template("home.html")

@app.route("/lobby")
def lobby():
    roomCode = session.get("roomCode")
    return render_template(
        "lobby.html", 
        players = [player["name"] + " " + player["emoji"] for player in rooms[roomCode]["players"] if player["inLobby"]],
        you = session["name"] + " (you) " + rooms[roomCode]["players"][session["name"]]["emoji"],
        code = roomCode
    )

@app.route("/game")
def game():
    return render_template("game.html")
    # Assign Roles

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

if __name__ == "__main__":
    socketio.run(app, debug=True)