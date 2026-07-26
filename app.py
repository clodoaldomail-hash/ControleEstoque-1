from flask import Flask, render_template, request, jsonify
import database

app = Flask(__name__)
app.config['SECRET_KEY'] = 'controle_estoques_access_secret_key_2026'

# Inicializar o banco de dados se necessário ao subir a aplicação
with app.app_context():
    try:
        database.init_db()
    except Exception as e:
        print(f"[ERRO INIT DB] {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

# --- API DE AUTENTICAÇÃO E USUÁRIOS ---

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json or {}
    usuario = data.get('usuario', '').strip()
    senha = data.get('senha', '').strip()
    
    if not usuario or not senha:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios.'}), 400
        
    try:
        user_info = database.autenticar_usuario(usuario, senha)
        if user_info:
            return jsonify({'success': True, 'user': user_info, 'message': 'Login realizado com sucesso!'})
        else:
            return jsonify({'success': False, 'message': 'Usuário ou senha incorretos.'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 403

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json or {}
    usuario = data.get('usuario', '').strip()
    senha = data.get('senha', '').strip()
    nome_usuario = data.get('nome_usuario', '').strip()
    nivel_acesso = data.get('nivel_acesso', 'Operador').strip()

    if not usuario or not senha or not nome_usuario:
        return jsonify({'success': False, 'message': 'Todos os campos obrigatórios devem ser preenchidos.'}), 400

    try:
        database.cadastrar_usuario(usuario, senha, nome_usuario, nivel_acesso, status_aprovacao="Pendente")
        return jsonify({'success': True, 'message': f'Usuário "{usuario}" cadastrado! Aguarde a aprovação do administrador para acessar o sistema.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/users', methods=['GET'])
def api_users():
    try:
        users = database.listar_usuarios()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/users/<int:id_usuario>/aprovar', methods=['POST'])
def api_aprovar_usuario(id_usuario):
    data = request.json or {}
    id_unidade = data.get('id_unidade')
    nivel_acesso = data.get('nivel_acesso', 'Operador')

    if not id_unidade:
        return jsonify({'success': False, 'message': 'Selecione uma Unidade Operacional para vincular ao usuário.'}), 400

    try:
        database.aprovar_usuario(id_usuario, id_unidade, nivel_acesso)
        return jsonify({'success': True, 'message': 'Usuário aprovado com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/users/<int:id_usuario>/editar', methods=['POST'])
def api_editar_usuario(id_usuario):
    data = request.json or {}
    id_unidade = data.get('id_unidade')
    nivel_acesso = data.get('nivel_acesso', 'Operador')

    if not id_unidade:
        return jsonify({'success': False, 'message': 'Selecione uma Unidade Operacional.'}), 400

    try:
        database.atualizar_usuario(id_usuario, id_unidade, nivel_acesso)
        return jsonify({'success': True, 'message': 'Unidade operacional do usuário atualizada com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/auth/users/<int:id_usuario>/rejeitar', methods=['POST'])
def api_rejeitar_usuario(id_usuario):
    try:
        database.rejeitar_usuario(id_usuario)
        return jsonify({'success': True, 'message': 'Cadastro do usuário rejeitado.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# --- API DE UNIDADES OPERACIONAIS ---

@app.route('/api/unidades', methods=['GET', 'POST'])
def api_unidades():
    if request.method == 'GET':
        try:
            unidades = database.listar_unidades()
            return jsonify({'success': True, 'unidades': unidades})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        data = request.json or {}
        id_unidade = data.get('id_unidade')
        nome = data.get('nome_unidade', '').strip()
        endereco = data.get('endereco', '').strip()
        cnpj = data.get('cnpj', '').strip()

        if not nome:
            return jsonify({'success': False, 'message': 'Nome da unidade é obrigatório.'}), 400

        try:
            if id_unidade:
                database.atualizar_unidade(id_unidade, nome, endereco, cnpj)
                msg = 'Unidade operacional atualizada!'
            else:
                database.cadastrar_unidade(nome, endereco, cnpj)
                msg = 'Unidade operacional cadastrada com sucesso!'
            return jsonify({'success': True, 'message': msg})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

# --- API DE DASHBOARD ---

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    id_unidade = request.args.get('id_unidade')
    if id_unidade and id_unidade.isdigit():
        id_unidade = int(id_unidade)
    else:
        id_unidade = None

    try:
        stats = database.obter_dados_dashboard(id_unidade=id_unidade)
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- API DE PRODUTOS ---

@app.route('/api/produtos', methods=['GET'])
def api_get_produtos():
    busca = request.args.get('busca', '').strip()
    categoria_id = request.args.get('categoria_id')
    if categoria_id and categoria_id.isdigit():
        categoria_id = int(categoria_id)
    else:
        categoria_id = None

    id_unidade = request.args.get('id_unidade')
    if id_unidade and id_unidade.isdigit():
        id_unidade = int(id_unidade)
    else:
        id_unidade = None

    try:
        produtos = database.listar_produtos(busca, categoria_id, id_unidade=id_unidade)
        return jsonify({'success': True, 'produtos': produtos})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos/<int:id_produto>', methods=['GET'])
def api_get_produto(id_produto):
    id_unidade = request.args.get('id_unidade')
    if id_unidade and id_unidade.isdigit():
        id_unidade = int(id_unidade)
    else:
        id_unidade = None

    try:
        produto = database.obter_produto_por_id(id_produto, id_unidade=id_unidade)
        if produto:
            return jsonify({'success': True, 'produto': produto})
        return jsonify({'success': False, 'message': 'Produto não encontrado.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/produtos', methods=['POST'])
def api_salvar_produto():
    data = request.json or {}
    if not data.get('nome_produto'):
        return jsonify({'success': False, 'message': 'O nome do produto é obrigatório.'}), 400

    try:
        database.salvar_produto(data)
        action = "atualizado" if data.get('id_produto') else "cadastrado"
        return jsonify({'success': True, 'message': f'Produto {action} com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/produtos/<int:id_produto>', methods=['DELETE'])
def api_excluir_produto(id_produto):
    try:
        database.excluir_produto(id_produto)
        return jsonify({'success': True, 'message': 'Produto excluído com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# --- API DE CATEGORIAS E FORNECEDORES ---

@app.route('/api/categorias', methods=['GET', 'POST'])
def api_categorias():
    if request.method == 'GET':
        try:
            categorias = database.listar_categorias()
            return jsonify({'success': True, 'categorias': categorias})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        data = request.json or {}
        nome = data.get('nome_categoria', '').strip()
        if not nome:
            return jsonify({'success': False, 'message': 'Nome da categoria é obrigatório.'}), 400
        try:
            database.cadastrar_categoria(nome)
            return jsonify({'success': True, 'message': 'Categoria cadastrada com sucesso!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/fornecedores', methods=['GET', 'POST'])
def api_fornecedores():
    if request.method == 'GET':
        try:
            fornecedores = database.listar_fornecedores()
            return jsonify({'success': True, 'fornecedores': fornecedores})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        data = request.json or {}
        nome = data.get('nome_fornecedor', '').strip()
        if not nome:
            return jsonify({'success': False, 'message': 'Nome do fornecedor é obrigatório.'}), 400
        try:
            database.cadastrar_fornecedor(
                nome,
                data.get('cnpj_cpf', ''),
                data.get('telefone', ''),
                data.get('email', '')
            )
            return jsonify({'success': True, 'message': 'Fornecedor cadastrado com sucesso!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

# --- API DE MOVIMENTAÇÕES DE ESTOQUE ---

@app.route('/api/movimentacoes', methods=['GET', 'POST'])
def api_movimentacoes():
    if request.method == 'GET':
        id_unidade = request.args.get('id_unidade')
        if id_unidade and id_unidade.isdigit():
            id_unidade = int(id_unidade)
        else:
            id_unidade = None

        try:
            movs = database.listar_movimentacoes(id_unidade=id_unidade)
            return jsonify({'success': True, 'movimentacoes': movs})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        data = request.json or {}
        id_produto = data.get('id_produto')
        tipo = data.get('tipo_movimentacao')
        qtd = data.get('quantidade')
        valor = data.get('valor_unitario', 0.0)
        obs = data.get('observacao', '')
        data_mov = data.get('data_movimentacao')
        id_unidade = data.get('id_unidade')

        if not id_produto or not tipo or not qtd:
            return jsonify({'success': False, 'message': 'Produto, tipo e quantidade são obrigatórios.'}), 400

        try:
            database.registrar_movimentacao(
                id_produto=id_produto,
                tipo_movimentacao=tipo,
                quantidade=qtd,
                valor_unitario=valor,
                observacao=obs,
                data_movimentacao=data_mov,
                id_unidade=id_unidade
            )
            return jsonify({'success': True, 'message': f'Movimentação de {tipo} registrada com sucesso!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    print("Iniciando servidor web Controle de Estoques - ITEC...")
    print("Acesse no navegador: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
