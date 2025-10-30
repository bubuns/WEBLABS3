import random
from functools import lru_cache
from flask import Flask, render_template
from faker import Faker

fake = Faker()

app = Flask(__name__)
application = app

images_ids = ['web-dev',
              'js-frameworks', 
              'database',
              'devops',
              'ai-unique']

post_titles = [
    'Введение в веб-разработку: с чего начать?',
    'Современные фреймворки JavaScript в 2024',
    'Основы работы с базами данных',
    'DevOps: автоматизация и развертывание',
    'Искусственный интеллект в программировании'
]

def generate_comments(replies=True):
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = { 'author': fake.name(), 'text': fake.text() }
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    programming_texts = [
        "Веб-разработка — это увлекательная область программирования, которая включает в себя создание веб-сайтов и веб-приложений. Современные технологии позволяют создавать интерактивные и динамические веб-страницы, используя HTML, CSS и JavaScript. Фреймворки и библиотеки значительно упрощают процесс разработки и повышают производительность.",
        
        "JavaScript остается одним из самых популярных языков программирования. В 2024 году появились новые фреймворки и инструменты, которые делают разработку еще более эффективной. React, Vue.js, Angular продолжают развиваться, предлагая разработчикам мощные инструменты для создания современных пользовательских интерфейсов.",
        
        "Базы данных являются основой большинства современных приложений. Понимание принципов работы с реляционными и NoSQL базами данных критически важно для любого разработчика. SQL остается стандартом для работы с данными, а новые технологии, такие как MongoDB и Redis, открывают новые возможности.",
        
        "DevOps — это культура и набор практик, которые объединяют разработку программного обеспечения и IT-операции. Автоматизация процессов, непрерывная интеграция и развертывание (CI/CD), контейнеризация с Docker и оркестрация с Kubernetes стали неотъемлемой частью современной разработки.",
        
        "Искусственный интеллект и машинное обучение революционизируют программирование. От автоматической генерации кода до интеллектуальных помощников разработчика — ИИ становится неотъемлемой частью процесса создания программного обеспечения. Понимание основ ИИ становится все более важным для современных программистов."
    ]
    
    return {
        'title': post_titles[i],
        'text': programming_texts[i],
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.svg',
        'comments': generate_comments()
    }

@lru_cache
def posts_list():
    return sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list())

@app.route('/posts/<int:index>')
def post(index):
    p = posts_list()[index]
    return render_template('post.html', title=p['title'], post=p)

@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
