import rule_engine
from flask import Flask, render_template, request

app = Flask(__name__)

def calcular_puntaje(cliente):
    puntaje = cliente["edad"]
    atributos_malos = ["diabetes", "hipertension", "fumador", "alcoholico", "reclamos_frecuentes", "minero", "piloto", "bombero"]
    for clave, valor in cliente.items():
        if str(valor).lower() in atributos_malos or valor == "true":
            puntaje += 4
    return puntaje

reglas_riesgo = {
    "bajo": rule_engine.Rule("puntaje < 30"),
    "moderado": rule_engine.Rule("puntaje >= 30 and puntaje <= 49"),
    "alto": rule_engine.Rule("puntaje > 49")
}

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        cliente = {
            "nombre": request.form["nombre"],
            "edad": int(request.form["edad"]),
            "salud": request.form["salud"],
            "historial_familiar": request.form["historial_familiar"],
            "estilo_vida": request.form["estilo_vida"],
            "ocupacion": request.form["ocupacion"],
            "historial_seguro": request.form["historial_seguro"]
        }
        
        cliente["puntaje"] = calcular_puntaje(cliente)

        # Se evalúa el puntaje con las reglas
        contexto = {"puntaje": cliente["puntaje"]}

        if reglas_riesgo["bajo"].evaluate(contexto):
            nivel_riesgo = "Bajo Riesgo"
        elif reglas_riesgo["moderado"].evaluate(contexto):
            nivel_riesgo = "Moderado Riesgo"
        elif reglas_riesgo["alto"].evaluate(contexto):
            nivel_riesgo = "Alto Riesgo"
        else:
            nivel_riesgo = "Desconocido"

        resultado = {
            "nombre": cliente["nombre"],
            "puntaje": cliente["puntaje"],
            "nivel_riesgo": nivel_riesgo
        }

    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
