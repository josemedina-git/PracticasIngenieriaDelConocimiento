import rule_engine
from flask import Flask, render_template, request


app = Flask(__name__)
    
def calcular_score(cliente):
    score = cliente["score_crediticio"]

    atributos_malos = {
        "ingresos_mensuales": ["menor a 1.5"],
        "dti": ["mas de 50"],
        "tipo_empleo": ["temporal"],
        "garantia": ["sin aval"],
        "historial_prestamos": ["impagos"]
    }

    atributos_moderados = {
        "ingresos_mensuales": ["1.5 a 3"],
        "dti": ["30 a 50"],
        "tipo_empleo": ["menos de 5"],
        "garantia": ["aval menor"],
        "historial_prestamos": ["retrasos ocasionales", "sin registro"]
    }

    for clave, valor in cliente.items():
        if clave in atributos_malos and valor in atributos_malos[clave]:
            score -= 35
        elif clave in atributos_moderados and valor in atributos_moderados[clave]:
            score -= 25
        elif clave not in ["nombre", "score_crediticio"]:
            score += 35 

    return score


reglas_score = {
    "aprobado": rule_engine.Rule("score > 750"),
    "aprobado_condicional": rule_engine.Rule("score >= 600 and score <= 750"),
    "rechazado": rule_engine.Rule("score < 600")
}

@app.route("/", methods=["GET", "POST"])
def index():
    score = None
    if request.method == "POST":
        cliente = {
            "nombre": request.form["nombre"],
            "score_crediticio": int(request.form["score_crediticio"]),
            "ingresos_mensuales": request.form["ingresos_mensuales"],
            "dti": request.form["dti"],
            "tipo_empleo": request.form["tipo_empleo"],
            "garantia": request.form["garantia"],
            "historial_prestamos": request.form["historial_prestamos"]
        }
        
        cliente["score"] = calcular_score(cliente)

        # Se evalúa el puntaje con las reglas
        contexto = {"score": cliente["score"]}

        if reglas_score["aprobado"].evaluate(contexto):
            nivel_riesgo = "Prestamo aprobado"
        elif reglas_score["aprobado_condicional"].evaluate(contexto):
            nivel_riesgo = "Prestamo aprobado condicional"
        elif reglas_score["rechazado"].evaluate(contexto):
            nivel_riesgo = "Prestamo rechazado"
        else:
            nivel_riesgo = "Prestamo pendiente"

        score = {
            "nombre": cliente["nombre"],
            "score": cliente["score"],
            "nivel_riesgo": nivel_riesgo
        }
    return render_template("index.html", score=score)

if __name__ == "__main__":
    app.run(debug=True)