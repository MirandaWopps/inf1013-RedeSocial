from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os

app = Flask(__name__)

# Arquivo para persistência dos dados
DATA_FILE = 'posts.json'

# Estrutura de dados para posts
def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# Inicializar posts
posts = load_posts()
if not posts:
    # Posts de exemplo
    posts = [
        {
            'id': 1,
            'username': 'Usuário Exemplo',
            'content': 'Este é um post de exemplo no meu feed de rede social!',
            'timestamp': '2026-05-19T15:35:36',
            'likes': 12,
            'dislikes': 3
        },
        {
            'id': 2,
            'username': 'Outro Usuário',
            'content': 'Adoro este novo recurso! #socialmedia #update',
            'timestamp': '2026-05-18T10:00:00',
            'likes': 25,
            'dislikes': 7
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
    """Retorna todos os posts"""
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    """Cria um novo post"""
    data = request.json
    new_post = {
        'id': len(posts) + 1,
        'username': data.get('username', 'Anônimo'),
        'content': data.get('content', ''),
        'timestamp': datetime.now().isoformat(),
        'likes': 0,
        'dislikes': 0
    }
    posts.insert(0, new_post)  # Adiciona no início
    save_posts(posts)
    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """Adiciona um like ao post"""
    for post in posts:
        if post['id'] == post_id:
            post['likes'] += 1
            save_posts(posts)
            return jsonify({'likes': post['likes']})
    return jsonify({'error': 'Post não encontrado'}), 404

@app.route('/api/posts/<int:post_id>/dislike', methods=['POST'])
def dislike_post(post_id):
    """Adiciona um dislike ao post"""
    for post in posts:
        if post['id'] == post_id:
            post['dislikes'] += 1
            save_posts(posts)
            return jsonify({'dislikes': post['dislikes']})
    return jsonify({'error': 'Post não encontrado'}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Deleta um post"""
    global posts
    posts = [post for post in posts if post['id'] != post_id]
    save_posts(posts)
    return jsonify({'message': 'Post deletado com sucesso'}), 200

# Rota principal - interface web
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Template HTML/CSS/JS
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

        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2em;
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

        .create-post button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }

        .create-post button:hover {
            transform: translateY(-2px);
        }

        .feed {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            gap: 15px;
            align-items: center;
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
            gap: 5px;
        }

        .like-btn {
            color: #4caf50;
        }

        .like-btn:hover {
            background: #e8f5e9;
            transform: scale(1.05);
        }

        .dislike-btn {
            color: #f44336;
        }

        .dislike-btn:hover {
            background: #ffebee;
            transform: scale(1.05);
        }

        .delete-btn {
            color: #999;
            margin-left: auto;
        }

        .delete-btn:hover {
            background: #ffebee;
            color: #f44336;
        }

        .stats {
            display: flex;
            gap: 5px;
            font-size: 12px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Rede Social</h1>
        </div>

        <div class="create-post">
            <input type="text" id="username" placeholder="Seu nome" maxlength="50">
            <textarea id="content" placeholder="O que você está pensando?"></textarea>
            <button onclick="createPost()">Publicar</button>
        </div>

        <div class="feed">
            <h2>Feed de Notícias</h2>
            <div id="posts-container"></div>
        </div>
    </div>

    <script>
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

            container.innerHTML = posts.map(post => `
                <div class="post" id="post-${post.id}">
                    <div class="post-header">
                        <span class="username">${escapeHtml(post.username)}</span>
                        <span class="timestamp">${formatTimestamp(post.timestamp)}</span>
                    </div>
                    <div class="post-content">${escapeHtml(post.content)}</div>
                    <div class="post-actions">
                        <button class="action-btn like-btn" onclick="handleLike(${post.id})">
                            👍 <span id="likes-${post.id}">${post.likes}</span>
                        </button>
                        <button class="action-btn dislike-btn" onclick="handleDislike(${post.id})">
                            👎 <span id="dislikes-${post.id}">${post.dislikes}</span>
                        </button>
                        <button class="action-btn delete-btn" onclick="deletePost(${post.id})">
                            🗑️ Deletar
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function createPost() {
            const username = document.getElementById('username').value.trim();
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
                        username: username || 'Anônimo',
                        content: content
                    })
                });

                if (response.ok) {
                    document.getElementById('username').value = '';
                    document.getElementById('content').value = '';
                    loadPosts();
                }
            } catch (error) {
                console.error('Erro ao criar post:', error);
                alert('Erro ao publicar. Tente novamente.');
            }
        }

        async function handleLike(postId) {
            try {
                const response = await fetch(`/api/posts/${postId}/like`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (response.ok) {
                    document.getElementById(`likes-${postId}`).textContent = data.likes;
                }
            } catch (error) {
                console.error('Erro ao dar like:', error);
            }
        }

        async function handleDislike(postId) {
            try {
                const response = await fetch(`/api/posts/${postId}/dislike`, {
                    method: 'POST'
                });
                const data = await response.json();
                if (response.ok) {
                    document.getElementById(`dislikes-${postId}`).textContent = data.dislikes;
                }
            } catch (error) {
                console.error('Erro ao dar dislike:', error);
            }
        }

        async function deletePost(postId) {
            if (confirm('Tem certeza que deseja deletar este post?')) {
                try {
                    const response = await fetch(`/api/posts/${postId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        loadPosts();
                    }
                } catch (error) {
                    console.error('Erro ao deletar post:', error);
                    alert('Erro ao deletar. Tente novamente.');
                }
            }
        }

        // Carregar posts ao iniciar
        loadPosts();

        // Atualizar feed a cada 30 segundos
        setInterval(loadPosts, 30000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)