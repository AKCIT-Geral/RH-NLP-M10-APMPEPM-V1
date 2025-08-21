#################################################################################################################
# Aplicação: Chunk_from_book
# Autor    : Sandrerley Ramos Pires                                              20/01/2025            
#            
# Finalida:  Esta aplicação tem como objetivo apresentar a interface web das aplicações aqui
#            implementadas. Ela apresenta uma tela no browser e encaminha ao servidor as 
#            solicitações do Chatbot e do Sistema de poio à Decisão.
#
#            O objetivo da aplicação é apenas exemplificar formas de se resolver um problema. Não há
#            uma preocupação profunda com a completa correteza dela, podendo em entradas diferentes das
#            utilizadas neste curso, ocorrerem problemas de execução.
#
#################################################################################################################
import requests
from datetime import datetime
import time
from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
import json

with open("extract_pdf.json", "r", encoding="utf-8") as f:
    book_data = json.load(f)
    book_title = book_data.get("title", "Livro não identificado")

# Relação de Livros a serem tratados
def send_message(user_question):
    API_URL = "http://localhost:8000/send"
    message = {
        "messagem":  0,
        "moment":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender":   "chatbot_fe",
        "receiver": "virtual_assistant_be",
        "control":  5,
        "content":  user_question+'@./virtual_assistant.json',    
        "log":      "False",
        "status":   "E"
        }
    response = requests.post(API_URL, json=message) 
    return response 

@app.route('/', methods=['GET', 'POST'])
def chatbot():
    user_question = ""
    bot_response = ""

    if request.method == 'POST':
        if 'submit' in request.form:
            question = request.form.get('question', '')
            response = send_message(question)
            
            # Simples lógica de exemplo de resposta
            API_URL = "http://localhost:8000/finished/" + str(response.json())
            start_time = time.time()
            max_seconds = 30
            while time.time() - start_time < max_seconds:
                resp = requests.get(API_URL) 
                if resp.json() !='Nok':                    
                    break
                time.sleep(1)
                
            if time.time() - start_time < max_seconds:
                bot_response = f"Você perguntou: '{question}'. \n\nResposta: {resp.json()}"
            else:
                bot_response = "Você perguntou: '{question}'. \n\n" + \
                               "Resposta: Tempo de espera da resposta está esgotado. Tente mais tarde."       
        elif 'exit' in request.form:
            return redirect(url_for('exit_app'))

    return render_template('chatbot.html', book_title=book_title, question=user_question, response=bot_response)

@app.route('/exit')
def exit_app():
    return "Aplicação encerrada. Obrigado por usar o chatbot!"

if __name__ == '__main__':
    app.run(debug=True)