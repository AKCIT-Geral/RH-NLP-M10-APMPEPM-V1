#################################################################################################################
# Aplicação:  virtual_assistant_be
# Autor     : Sandrerley Ramos Pires                                                  02/01/2025
#            
# Finalidade: Esta aplicação tem como objetivo receber uma pergunta do usuário e respondê-la de acordo
#             com o conteúdo extraído de um livro em PDF. Para tanto, executa os seguintes passos:
#             1) Calcula o Embedding da pergunta
#             2) busca subsídios para respondê-la na base de comhecimento 
#             3) monta o prompt para formalizar o pedido à LLM
#             4) recebe a resposta e a envia de volta ao cliente.
#
#             O objetivo da aplicação é apenas exemplificar formas de se resolver um problema. Não há
#             uma preocupação profunda com a completa correteza dela, podendo em entradas diferentes das
#             utilizadas neste curso, ocorrerem problemas de execução.
#
#################################################################################################################
import chromadb
import json
import os
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
genai.configure(api_key="SUA-KEY")

# Efetua a inicialização da coleção no Chromadb
def conect_chromadb(local_bd, collection_name):
    try:
        #Cria instância para acesso ao Chromadb
        chroma_client = chromadb.PersistentClient(local_bd)
        
        # Acessa a coleção, caso ela não exista, ela é criada.
        collection = chroma_client.get_or_create_collection(name=collection_name)
        
        return True, "ok", chroma_client, collection
    except:
        resp = "Problema na conexão da coleção. Confira instalação do Cromadb."
        return False, resp, None, None    
    
# Gera conteúdos obtidos a partir de cálculo de proximidade de Embeddings
def gera_contend(question, local_bd, collections_name):
    # Cria classe para cálculo de embeddings
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embedding = model.encode(question)
    contend = ''
    for collection_name in collections_name:
        Ok, resp, chroma_client, collection = conect_chromadb(local_bd, collection_name)
        if not Ok:
            return False, 'Deu problema na conexão com o Chroma. Veja arquivo de parâmetros'
        else:
            results = collection.query(query_embeddings=[embedding], n_results=20)
            for i in range(0, len(results['documents'][0])):
                if abs(results['distances'][0][i] - 1) < 0.3:
                    contend = contend + results['documents'][0][i] + '\n\n'
                    
    return True, contend    
    
# Monta o promptque sera usado para chamar a LLM
def monta_prompt(question, contend, prompt_model):
    texto = prompt_model.replace('<question>', question)
    texto = texto.replace('<contend>', contend)
    prompt = texto
    return prompt

# Submete o promppt ao LLM
def call_LLM(prompt):
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
    result = model.generate_content(prompt)
    return result.text

# Efetua a leitura dos parâmetro informados pelo cliente
def param(message):
    # obtem o questionamento e o nome do arquivo de parâmetros
    [question, parm_file] = message.split('@')
    if not os.path.exists(parm_file):
       resp = "O arquivo de parâmetros não existe:" + parm_file
       return False, resp, None, None, None, None
    else:
        with open(parm_file, 'r', encoding='utf-8') as fp:
            parametros = json.load(fp)
            try:                
                prompt_model = parametros['prompt']                
                local_bd     = parametros['local_bd'] 
                collections_name = parametros['collection'] 
            except:
                resp = "Problema na obtenção dos parâmetros. Possível arquivo inválido."
                return False, resp, None, None, None,None
            
    return True, "Ok", question, prompt_model, local_bd, collections_name
    
#
#  Executa a sequência de tarefas do assistente virtual
#
def _virtual_assistant_be(nmsg, message):
    # Efetua a leitura dos parâmetro informados pelo cliente
    Ok, resp, question, prompt_model, local_bd, collections_name = param(message)
    if Ok:
        # obtém uma relação de conteúdos que são semanticamente próximos da resposta
        ok, contend = gera_contend(question, local_bd, collections_name)
        if ok:
            if contend =='':
                return nmsg, True, 'Não sei responder. Pergunte outra coisa.'
            else:
                prompt = monta_prompt(question, contend, prompt_model)
                resp   = call_LLM(prompt)
                return nmsg, True, resp
        else:
            return nmsg, False, contend # usei a variável contend para trazer a descrição do erro
    else:
        return nmsg, False, 'Não conseguiu acessar os dados do arquivo de parâmetros'
    