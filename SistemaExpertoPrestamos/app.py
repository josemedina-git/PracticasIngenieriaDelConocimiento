import rule_engine
from flask import Flask, render_template, request

app = Flask(__name__)

# Definir reglas para modificar el score
reglas_modificacion = {
    "ingresos_mensuales == 'menor a 1.5'": -35,
    "ingresos_mensuales == '1.5 a 3'": -25,
    "garantia == 'aval mayor'": 200,
    "garantia == 'sin aval'": -35,
    "tipo_empleo == 'temporal'": -35,
    "tipo_empleo == 'menos de 5'": -25,
    "historial_prestamos == 'impagos'": -35,
    "historial_prestamos in ['retrasos ocasionales', 'sin registro']": -25,
    "dti == 'mas de 50'": -35,
    "dti == '30 a 50'": -25
}

# Reglas para determinar el estado del préstamo
reglas_score = {
    "aprobado": rule_engine.Rule("score > 750"),
    "aprobado_condicional": rule_engine.Rule("score >= 600 and score <= 750"),
    "rechazado": rule_engine.Rule("score < 600")
}

def calcular_score(cliente):
    contexto = {"score": cliente["score_crediticio"], **cliente}
    
    for expresion, modificador in reglas_modificacion.items():
        if rule_engine.Rule(expresion).evaluate(contexto):
            contexto["score"] += modificador
    
    return contexto["score"]

@app.route("/", methods=["GET", "POST"])
def index():
    score = None
    if request.method == "POST":
        try:
            ingresos_mensuales = float(request.form["ingresos_mensuales"])
            monto_prestamo = float(request.form["monto_prestamo"])
            meses_prestamo = int(request.form["meses_prestamo"])

            # Calcular cuota mensual
            cuota_prestamo = monto_prestamo / meses_prestamo

            # Determinar la categoría de ingresos
            if ingresos_mensuales >= cuota_prestamo * 3:
                categoria_ingresos = "mayor a 3"
            elif ingresos_mensuales >= cuota_prestamo * 1.5:
                categoria_ingresos = "1.5 a 3"
            else:
                categoria_ingresos = "menor a 1.5"

            cliente = {
                "nombre": request.form["nombre"],
                "score_crediticio": int(request.form["score_crediticio"]),
                "ingresos_mensuales": categoria_ingresos,
                "dti": request.form["dti"],
                "tipo_empleo": request.form["tipo_empleo"],
                "garantia": request.form["garantia"],
                "historial_prestamos": request.form["historial_prestamos"]
            }

            cliente["score"] = calcular_score(cliente)
            contexto = {"score": cliente["score"]}

            if reglas_score["aprobado"].evaluate(contexto):
                nivel_riesgo = "Prestamo aprobado"
            elif reglas_score["aprobado_condicional"].evaluate(contexto):
                nivel_riesgo = "Prestamo aprobado condicional"
            else:
                nivel_riesgo = "Prestamo rechazado"

            score = {
                "nombre": cliente["nombre"],
                "score": cliente["score"],
                "nivel_riesgo": nivel_riesgo,
                "cuota_mensual": round(cuota_prestamo, 2)
            }
        except KeyError as e:
            print(f"Error: Falta el campo {e}")
            return "Error: Faltan campos en el formulario", 400

    return render_template("index.html", score=score)

if __name__ == "__main__":
    app.run(debug=True)