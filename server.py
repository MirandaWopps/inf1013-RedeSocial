from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'temporary_data_key'

# Arquivos para persistência dos dados
DATA_FILE = 'posts.json'
USERS_FILE = 'users.json'
FRIEND_REQUESTS_FILE = 'friend_requests.json'

# Estrutura de dados para posts
def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# Estrutura de dados para usuários
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# Estrutura de dados para envio de pedidos de amizade
def load_friend_requests():
    if os.path.exists(FRIEND_REQUESTS_FILE):
        with open(FRIEND_REQUESTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_friend_requests(friend_requests):
    with open(FRIEND_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(friend_requests, f, ensure_ascii=False, indent=2)

# Inicializar dados
posts = load_posts()
users = load_users()
friend_requests = load_friend_requests()

if not posts:
    # Posts de exemplo
    posts = [
        {
            'id': 1,
            'username': 'Maria Silva',
            'content': 'Acabei de lançar meu novo projeto! Estou muito animada para compartilhar isso com vocês. 🎉',
            'timestamp': '2026-06-05T09:00:00',
            'likes': 124,
            'comments': 18,
            'shares': 5
        },
        {
            'id': 2,
            'username': 'João Santos',
            'content': 'Bom dia! Começando a semana com energia positiva. ☀️',
            'timestamp': '2026-06-05T06:00:00',
            'likes': 43,
            'comments': 7,
            'shares': 2
        }
    ]
    save_posts(posts)

def format_time_ago(timestamp):
    """Formata o timestamp para 'X horas/minutos atrás'"""
    try:
        post_time = datetime.fromisoformat(timestamp)
        now = datetime.now()
        diff = now - post_time
        
        if diff.days > 0:
            if diff.days == 1:
                return "Ontem"
            return f"{diff.days} dias atrás"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} horas atrás" if hours > 1 else "1 hora atrás"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutos atrás" if minutes > 1 else "1 minuto atrás"
        else:
            return "Agora mesmo"
    except:
        return timestamp

# Rotas da API
@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Retorna posts visíveis para o usuário logado"""
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']

    visible_posts = []

    for post in posts:
        if not post.get('is_share'):
            visible_posts.append(post)
        else:
            if current_user in post.get('shared_to', []):
                visible_posts.append(post)

    return jsonify(visible_posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    """Cria um novo post"""
    data = request.json
    new_post = {
        'id': len(posts) + 1,
        'username': session['username'],
        'content': data.get('content', ''),
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'comments': 0,
        'shares': 0,
        'is_share': data.get('is_share', False),
        'original_author': data.get('original_author', None)
    }
    posts.insert(0, new_post)  # Adiciona no início
    save_posts(posts)
    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
def share_post(post_id):
    """Compartilha um post com amigos selecionados"""
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']
    data = request.json
    selected_friends = data.get('selected_friends', [])

    if not selected_friends:
        return jsonify({'error': 'Selecione pelo menos um amigo para compartilhar'}), 400

    current_user_data = None
    for user in users:
        if user['username'] == current_user:
            current_user_data = user
            break

    if not current_user_data:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    current_user_friends = current_user_data.get('friends', [])

    for friend in selected_friends:
        if friend not in current_user_friends:
            return jsonify({'error': f'{friend} não é seu amigo'}), 400

    original_post = None
    for post in posts:
        if post['id'] == post_id:
            original_post = post
            break

    if not original_post:
        return jsonify({'error': 'Post não encontrado'}), 404

    original_post['shares'] = original_post.get('shares', 0) + 1

    shared_post = {
        'id': len(posts) + 1,
        'username': current_user,
        'content': original_post['content'],
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'liked_by': [],
        'comments': 0,
        'shares': 0,
        'is_share': True,
        'original_author': original_post['username'],
        'original_post_id': original_post['id'],
        'shared_to': selected_friends
    }

    posts.insert(0, shared_post)
    save_posts(posts)

    return jsonify(shared_post), 201

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Alterna curtida do usuário logado no post"""
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']

    for post in posts:
        if post['id'] == post_id:
            if 'liked_by' not in post:
                post['liked_by'] = []

            if current_user in post['liked_by']:
                post['liked_by'].remove(current_user)
            else:
                post['liked_by'].append(current_user)

            post['likes'] = len(post['liked_by'])
            save_posts(posts)

            return jsonify({
                'likes': post['likes'],
                'liked_by_current_user': current_user in post['liked_by']
            })

    return jsonify({'error': 'Post não encontrado'}), 404

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    """Adiciona um comentário ao post"""
    data = request.json
    for post in posts:
        if post['id'] == post_id:
            post['comments'] = post.get('comments', 0) + 1
            save_posts(posts)
            return jsonify({'comments': post['comments']})
    return jsonify({'error': 'Post não encontrado'}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Deleta um post"""
    global posts
    posts = [post for post in posts if post['id'] != post_id]
    save_posts(posts)
    return jsonify({'message': 'Post deletado com sucesso'}), 200

# Rotas de Login e Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))

        return render_template_string(LOGIN_TEMPLATE, error='Usuário ou senha inválidos.')

    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Rota de listar usuários
@app.route('/api/users', methods=['GET'])
def get_users():
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']

    visible_users = []
    for user in users:
        if user['username'] != current_user:
            visible_users.append({
                'username': user['username'],
                'friends': current_user in user.get('friends', [])
            })

    return jsonify(visible_users)

# Rota de envio de convite de amizade
@app.route('/api/friend-request/<target_username>', methods=['POST'])
def send_friend_request(target_username):
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']

    if current_user == target_username:
        return jsonify({'error': 'Você não pode enviar solicitação para si mesmo'}), 400

    target_user = None
    for user in users:
        if user['username'] == target_username:
            target_user = user
            break

    if not target_user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    current_user_data = None
    for user in users:
        if user['username'] == current_user:
            current_user_data = user
            break

    if target_username in current_user_data.get('friends', []):
        return jsonify({'error': 'Vocês já são amigos'}), 400

    for req in friend_requests:
        if (
            req['from'] == current_user
            and req['to'] == target_username
            and req['status'] == 'pending'
        ):
            return jsonify({'error': 'Solicitação já enviada'}), 400

    new_request = {
        'from': current_user,
        'to': target_username,
        'status': 'pending',
        'timestamp': datetime.now().isoformat()
    }

    friend_requests.append(new_request)
    save_friend_requests(friend_requests)

    return jsonify({'message': 'Solicitação enviada com sucesso'})

# Rotas de listar e responder solicitações de amizade
@app.route('/api/friend-requests', methods=['GET'])
def get_friend_requests():
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']

    received_requests = [
        req for req in friend_requests
        if req['to'] == current_user and req['status'] == 'pending'
    ]

    return jsonify(received_requests)

@app.route('/api/friend-request/respond', methods=['POST'])
def respond_friend_request():
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']
    data = request.json

    from_user = data.get('from')
    action = data.get('action')

    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Ação inválida'}), 400

    for req in friend_requests:
        if req['from'] == from_user and req['to'] == current_user and req['status'] == 'pending':
            if action == 'accept':
                req['status'] = 'accepted'

                for user in users:
                    if user['username'] == current_user:
                        if from_user not in user['friends']:
                            user['friends'].append(from_user)

                    if user['username'] == from_user:
                        if current_user not in user['friends']:
                            user['friends'].append(current_user)

                save_users(users)

            else:
                req['status'] = 'rejected'

            save_friend_requests(friend_requests)

            return jsonify({'message': 'Solicitação respondida com sucesso'})

    return jsonify({'error': 'Solicitação não encontrada'}), 404

# Rota para listar amigos
@app.route('/api/friends', methods=['GET'])
def get_friends():
    if 'username' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401

    current_user = session['username']

    for user in users:
        if user['username'] == current_user:
            return jsonify(user.get('friends', []))

    return jsonify([])

# Rota principal - interface web
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template_string(
        HTML_TEMPLATE,
        current_user=session['username']
    )

# Templates HTML/CSS/JS
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Login - Rede Social</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }

        .login-box {
            background: white;
            padding: 30px;
            border-radius: 12px;
            width: 320px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        h1 {
            margin-bottom: 20px;
            color: #333;
            text-align: center;
        }

        input {
            width: 100%;
            padding: 12px;
            margin-bottom: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
        }

        button {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: #667eea;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        .error {
            color: #f44336;
            margin-bottom: 12px;
            text-align: center;
        }

        .hint {
            margin-top: 15px;
            font-size: 13px;
            color: #666;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>📱 Login</h1>

        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <input type="text" name="username" placeholder="Usuário" required>
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit">Entrar</button>
        </form>

        <div class="hint">
            Teste: pedro / 123<br>
            lucas / 123<br>
            maria / 123<br>
            joao / 123
        </div>
    </div>
</body>
</html>
'''



HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rede Social</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2em;
        }
        
        .user-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 25px;
            font-size: 18px;
            color: #333;
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .current-user {
            font-size: 26px;
            font-weight: 800;
            color: #764ba2;
            letter-spacing: 0.5px;
        }
        
        .user-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }

        .user-item:last-child {
            border-bottom: none;
        }

        .user-name {
            font-weight: bold;
            color: #667eea;
        }
        
        .friend-status {
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            padding: 12px 24px;
            display: inline-block;
        }

        .logout-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }

        .logout-btn:hover {
            transform: translateY(-2px);
            text-decoration: none;
        }

        .create-post {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .create-post input,
        .create-post textarea {
            width: 100%;
            padding: 12px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
        }

        .create-post textarea {
            min-height: 100px;
            resize: vertical;
        }

        .primary-btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
            text-decoration: none;
            text-align: center;
        }

        .primary-btn:hover {
            transform: translateY(-2px);
            text-decoration: none;
        }

        .feed {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .feed h2 {
            margin-bottom: 20px;
            color: #333;
        }

        .post {
            border-bottom: 1px solid #eee;
            padding: 20px 0;
            transition: background 0.2s;
        }

        .post:last-child {
            border-bottom: none;
        }

        .post:hover {
            background: #f9f9f9;
            padding-left: 10px;
            padding-right: 10px;
        }

        .share-indicator {
            background: #f0f2f5;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 13px;
            color: #65676b;
        }

        .share-indicator i {
            margin-right: 5px;
        }

        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .username {
            font-weight: bold;
            color: #667eea;
            font-size: 16px;
        }

        .timestamp {
            color: #999;
            font-size: 12px;
        }

        .post-content {
            color: #333;
            line-height: 1.5;
            margin-bottom: 15px;
            word-wrap: break-word;
        }

        .post-actions {
            display: flex;
            gap: 20px;
            align-items: center;
            margin-top: 10px;
        }

        .action-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #65676b;
        }

        .action-btn:hover {
            background: #f0f2f5;
        }

        .like-btn:hover {
            color: #4caf50;
        }

        .comment-btn:hover {
            color: #2196f3;
        }

        .share-btn:hover {
            color: #9c27b0;
        }

        .stats {
            font-size: 13px;
            color: #65676b;
        }

        .empty-feed {
            text-align: center;
            color: #999;
            padding: 40px;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .post {
            animation: fadeIn 0.3s ease-out;
        }

        .share-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .share-modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 400px;
            width: 90%;
        }

        .share-modal-content h3 {
            margin-bottom: 20px;
        }

        .share-modal-content input {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 6px;
        }

        .modal-description {
            color: #555;
            font-size: 14px;
            margin-bottom: 15px;
        }

        .share-friend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }

        .share-friend-item:last-child {
            border-bottom: none;
        }

        .share-friend-item label {
            cursor: pointer;
            font-weight: bold;
            color: #667eea;
        }
        
        .modal-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }

        .modal-buttons button {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }

        .modal-buttons button:first-child {
            background: #ddd;
        }

        .modal-buttons button:last-child {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-top">
                <h1>📱 Rede Social</h1>

                <button class="primary-btn" onclick="openFriendsModal()">Amigos</button>
            </div>

            <div class="user-bar">
                <div class="user-info">
                    <span>Logado como:</span>
                    <strong class="current-user">{{ current_user }}</strong>
                </div>

                <div class="user-actions">
                    <button class="primary-btn" onclick="openUsersModal()">Adicionar amigos</button>
                    <button class="primary-btn" onclick="openRequestsModal()">Solicitações</button>
                    <a class="primary-btn" href="/logout">Sair</a>
                </div>
            </div>
        </div>
        <div class="create-post">
            <textarea id="content" placeholder="O que você está pensando?"></textarea>
            <button class="primary-btn" onclick="createPost()">Publicar</button>
        </div>

        <div class="feed">
            <h2>Feed</h2>
            <div id="posts-container"></div>
        </div>
    </div>

    <!-- Modal de Solicitações de Amizade -->
    <div id="requestsModal" class="share-modal">
        <div class="share-modal-content">
            <h3>Solicitações recebidas</h3>
            <div id="requests-container"></div>
            <div class="modal-buttons">
                <button onclick="closeRequestsModal()">Fechar</button>
            </div>
        </div>
    </div>
    
    <!-- Modal de Amigos -->
    <div id="friendsModal" class="share-modal">
        <div class="share-modal-content">
            <h3>Meus amigos</h3>
            <div id="friends-container"></div>
            <div class="modal-buttons">
                <button onclick="closeFriendsModal()">Fechar</button>
            </div>
        </div>
    </div>
    
    <!-- Modal de Compartilhamento -->
    <div id="shareModal" class="share-modal">
        <div class="share-modal-content">
            <h3>Compartilhar Post</h3>
            <p class="modal-description">Selecione os amigos que receberão este compartilhamento:</p>

            <div id="share-friends-container"></div>

            <div class="modal-buttons">
                <button onclick="closeShareModal()">Cancelar</button>
                <button onclick="confirmShare()">Compartilhar</button>
            </div>
        </div>
    </div>
    
    <!-- Modal de Usuário -->
    <div id="usersModal" class="share-modal">
        <div class="share-modal-content">
            <h3>Adicionar amigos</h3>
            <div id="users-container"></div>
            <div class="modal-buttons">
                <button onclick="closeUsersModal()">Fechar</button>
            </div>
        </div>
    </div>

    <script>
        let currentSharePostId = null;

        function openRequestsModal() {
            document.getElementById('requestsModal').style.display = 'flex';
            loadFriendRequests();
        }

        // Funções de solicitação de amizade
        function closeRequestsModal() {
            document.getElementById('requestsModal').style.display = 'none';
        }

        async function loadFriendRequests() {
            try {
                const response = await fetch('/api/friend-requests');
                const requests = await response.json();
                displayFriendRequests(requests);
            } catch (error) {
                console.error('Erro ao carregar solicitações:', error);
            }
        }

        function displayFriendRequests(requests) {
            const container = document.getElementById('requests-container');

            if (requests.length === 0) {
                container.innerHTML = '<div class="empty-feed">Nenhuma solicitação pendente.</div>';
                return;
            }

            container.innerHTML = requests.map(req => `
                <div class="user-item">
                    <span class="user-name">${escapeHtml(req.from)}</span>
                    <div class="user-actions">
                        <button class="primary-btn" onclick="respondFriendRequest('${escapeHtml(req.from)}', 'accept')">
                            Aceitar
                        </button>
                        <button class="primary-btn" onclick="respondFriendRequest('${escapeHtml(req.from)}', 'reject')">
                            Recusar
                        </button>
                    </div>
                </div>
            `).join('');
        }

        async function respondFriendRequest(fromUser, action) {
            try {
                const response = await fetch('/api/friend-request/respond', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        from: fromUser,
                        action: action
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    alert(data.message);
                    loadFriendRequests();
                    loadUsers();
                } else {
                    alert(data.error || 'Erro ao responder solicitação.');
                }
            } catch (error) {
                console.error('Erro ao responder solicitação:', error);
            }
        }
        
        // Funções de listar amigos
        function openFriendsModal() {
            document.getElementById('friendsModal').style.display = 'flex';
            loadFriends();
        }

        function closeFriendsModal() {
            document.getElementById('friendsModal').style.display = 'none';
        }

        async function loadFriends() {
            try {
                const response = await fetch('/api/friends');
                const friends = await response.json();
                displayFriends(friends);
            } catch (error) {
                console.error('Erro ao carregar amigos:', error);
            }
        }

        function displayFriends(friends) {
            const container = document.getElementById('friends-container');

            if (friends.length === 0) {
                container.innerHTML = '<div class="empty-feed">Você ainda não tem amigos adicionados.</div>';
                return;
            }

            container.innerHTML = friends.map(friend => `
                <div class="user-item">
                    <span class="user-name">${escapeHtml(friend)}</span>
                </div>
            `).join('');
        }
        
        
        
        
        async function loadPosts() {
            try {
                const response = await fetch('/api/posts');
                const posts = await response.json();
                displayPosts(posts);
            } catch (error) {
                console.error('Erro ao carregar posts:', error);
            }
        }

        function formatTimestamp(timestamp) {
            const postDate = new Date(timestamp);
            const now = new Date();
            const diffTime = Math.abs(now - postDate);
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
            const diffMinutes = Math.floor(diffTime / (1000 * 60));

            if (diffDays > 0) {
                return diffDays === 1 ? 'Ontem' : `${diffDays} dias atrás`;
            } else if (diffHours > 0) {
                return `${diffHours} ${diffHours === 1 ? 'hora' : 'horas'} atrás`;
            } else if (diffMinutes > 0) {
                return `${diffMinutes} ${diffMinutes === 1 ? 'minuto' : 'minutos'} atrás`;
            } else {
                return 'Agora mesmo';
            }
        }

        function displayPosts(posts) {
            const container = document.getElementById('posts-container');
            
            if (posts.length === 0) {
                container.innerHTML = '<div class="empty-feed">Nenhum post ainda. Seja o primeiro a publicar!</div>';
                return;
            }

            container.innerHTML = posts.map(post => {
                let shareHtml = '';
                if (post.is_share) {
                    shareHtml = `
                        <div class="share-indicator">
                            🔄 ${escapeHtml(post.username)} compartilhou de ${escapeHtml(post.original_author)}
                        </div>
                    `;
                }

                return `
                    <div class="post" id="post-${post.id}">
                        ${shareHtml}
                        <div class="post-header">
                            <span class="username">${post.is_share ? '' : escapeHtml(post.username)}</span>
                            <span class="timestamp">${formatTimestamp(post.timestamp)}</span>
                        </div>
                        <div class="post-content">${escapeHtml(post.content)}</div>
                        <div class="stats">
                            ❤️ ${post.likes}   💬 ${post.comments}   🔄 ${post.shares || 0}
                        </div>
                        <div class="post-actions">
                            <button class="action-btn like-btn" onclick="handleLike(${post.id})">
                                👍 Curtir
                            </button>
                            <button class="action-btn comment-btn" onclick="handleComment(${post.id})">
                                💬 Comentar
                            </button>
                            <button class="action-btn share-btn" onclick="openShareModal(${post.id})">
                                🔄 Compartilhar
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function createPost() {
            const content = document.getElementById('content').value.trim();

            if (!content) {
                alert('Por favor, escreva algo para publicar!');
                return;
            }

            try {
                const response = await fetch('/api/posts', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        content: content,
                        is_share: false
                    })
                });

                if (response.ok) {
                    document.getElementById('content').value = '';
                    loadPosts();
                }
            } catch (error) {
                console.error('Erro ao criar post:', error);
                alert('Erro ao publicar. Tente novamente.');
            }
        }

        async function openShareModal(postId) {
            currentSharePostId = postId;
            document.getElementById('shareModal').style.display = 'flex';

            await loadFriendsForShare();
        }
        
        async function loadFriendsForShare() {
            const container = document.getElementById('share-friends-container');

            try {
                const response = await fetch('/api/friends');
                const friends = await response.json();

                if (friends.length === 0) {
                    container.innerHTML = '<div class="empty-feed">Você ainda não possui amigos para compartilhar posts.</div>';
                    return;
                }

                container.innerHTML = friends.map(friend => `
                    <div class="share-friend-item">
                        <input type="checkbox" class="share-friend-checkbox" value="${escapeHtml(friend)}" id="share-${escapeHtml(friend)}">
                        <label for="share-${escapeHtml(friend)}">${escapeHtml(friend)}</label>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Erro ao carregar amigos para compartilhamento:', error);
                container.innerHTML = '<div class="empty-feed">Erro ao carregar amigos.</div>';
            }
        }

        function closeShareModal() {
            document.getElementById('shareModal').style.display = 'none';
            currentSharePostId = null;
        }
        
        function openUsersModal() {
            document.getElementById('usersModal').style.display = 'flex';
            loadUsers();
        }

        function closeUsersModal() {
            document.getElementById('usersModal').style.display = 'none';
        }

        async function confirmShare() {
            if (!currentSharePostId) return;

            const selectedFriends = Array.from(
                document.querySelectorAll('.share-friend-checkbox:checked')
            ).map(checkbox => checkbox.value);

            if (selectedFriends.length === 0) {
                alert('Selecione pelo menos um amigo para compartilhar.');
                return;
            }

            try {
                const response = await fetch(`/api/posts/${currentSharePostId}/share`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        selected_friends: selectedFriends
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Post compartilhado com sucesso!');
                    closeShareModal();
                    loadPosts();
                } else {
                    alert(data.error || 'Erro ao compartilhar. Tente novamente.');
                }
            } catch (error) {
                console.error('Erro ao compartilhar:', error);
                alert('Erro ao compartilhar. Tente novamente.');
            }
        }

        async function handleLike(postId) {
            try {
                const response = await fetch(`/api/posts/${postId}/like`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadPosts();
                }
            } catch (error) {
                console.error('Erro ao dar like:', error);
            }
        }

        async function handleComment(postId) {
            const comment = prompt('Digite seu comentário:');
            if (comment && comment.trim()) {
                try {
                    const response = await fetch(`/api/posts/${postId}/comment`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ comment: comment })
                    });
                    if (response.ok) {
                        alert('Comentário adicionado!');
                        loadPosts();
                    }
                } catch (error) {
                    console.error('Erro ao comentar:', error);
                }
            }
        }

        // Fechar modal ao clicar fora
        window.onclick = function(event) {
            const shareModal = document.getElementById('shareModal');
            const usersModal = document.getElementById('usersModal');
            const requestsModal = document.getElementById('requestsModal');
            const friendsModal = document.getElementById('friendsModal');
            
            if (event.target === shareModal) {
                closeShareModal();
            }

            if (event.target === usersModal) {
                closeUsersModal();
            }
            
            if (event.target === requestsModal) {
                closeRequestsModal();
            }
            
            if (event.target === friendsModal) {
                closeFriendsModal();
            }
        }
        
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const users = await response.json();
                displayUsers(users);
            } catch (error) {
                console.error('Erro ao carregar usuários:', error);
            }
        }

        function displayUsers(users) {
            const container = document.getElementById('users-container');

            if (users.length === 0) {
                container.innerHTML = '<div class="empty-feed">Nenhum outro usuário encontrado.</div>';
                return;
            }

            container.innerHTML = users.map(user => `
                <div class="user-item">
                    <span class="user-name">${escapeHtml(user.username)}</span>
                    ${
                        user.friends
                        ? `<span class="friend-status">Vocês já são amigos</span>`
                        : `<button class="primary-btn" onclick="sendFriendRequest('${escapeHtml(user.username)}')">
                            Enviar Solicitação
                        </button>`
                    }
                </div>
            `).join('');
        }

        async function sendFriendRequest(username) {
            try {
                const response = await fetch(`/api/friend-request/${username}`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (response.ok) {
                    alert('Solicitação enviada com sucesso!');
                } else {
                    alert(data.error || 'Erro ao enviar solicitação.');
                }
            } catch (error) {
                console.error('Erro ao enviar solicitação:', error);
                alert('Erro ao enviar solicitação.');
            }
        }

        // Carregar posts ao iniciar
        loadPosts();
        loadUsers();

        // Atualizar feed a cada 30 segundos
        setInterval(loadPosts, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)