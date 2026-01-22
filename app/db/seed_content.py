"""Seed database with sample content."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.base import SessionLocal
from app.models.category import Category
from app.models.content import Content, ContentStatus, ContentType
from app.models.user import User, UserRole


def create_sample_users(db: Session) -> dict[str, User]:
    """Create sample users for different roles."""
    users = {}
    
    # Editor
    editor = db.query(User).filter(User.email == "editor@qazaq.kz").first()
    if not editor:
        editor = User(
            username="editor",
            email="editor@qazaq.kz",
            first_name="Айдар",
            last_name="Нұрланов",
            hashed_password=get_password_hash("editor123"),
            role=UserRole.EDITOR,
            is_active=True,
            bio="Журналист с 10-летним опытом работы в казахстанских СМИ"
        )
        db.add(editor)
        print("✓ Created editor user")
    users["editor"] = editor
    
    # Another editor
    editor2 = db.query(User).filter(User.email == "editor2@qazaq.kz").first()
    if not editor2:
        editor2 = User(
            username="editor2",
            email="editor2@qazaq.kz",
            first_name="Асель",
            last_name="Қайратова",
            hashed_password=get_password_hash("editor123"),
            role=UserRole.EDITOR,
            is_active=True,
            bio="Специалист по экономической журналистике"
        )
        db.add(editor2)
        print("✓ Created second editor user")
    users["editor2"] = editor2
    
    db.commit()
    db.refresh(editor)
    db.refresh(editor2)
    
    return users


def create_sample_news(db: Session, users: dict[str, User], categories: dict[str, Category]) -> None:
    """Create sample news articles."""
    
    news_data = [
        {
            "title": "Қазақстанда жаңа технопарк ашылды",
            "content": """# Астанада инновациялық технопарк ашылды

Бүгін Астанада жаңа инновациялық технопарк салтанатты түрде ашылды. Технопарк отандық IT-стартаптарға қолдау көрсету және цифрлық экономиканы дамыту мақсатында құрылған.

## Негізгі мақсаттар

Технопарктың басты міндеттері:
- Жас кәсіпкерлерге қолдау көрсету
- Инновациялық жобаларды қаржыландыру
- Халықаралық серіктестікті дамыту

Технопарк аумағында заманауи офистер, конференц-залдар және коворкинг кеңістіктері орналасқан.

## Болашақ жоспарлар

Алдағы үш жыл ішінде технопарк 500-ден астам жұмыс орнын ашуды жоспарлап отыр.""",
            "excerpt": "Астанада отандық IT-стартаптарға қолдау көрсету мақсатында жаңа инновациялық технопарк ашылды.",
            "category": "technology",
            "author": "editor"
        },
        {
            "title": "Қазақстан экономикасы тұрақты өсуде",
            "content": """# Қазақстан экономикасы 2025 жылы 5% өсті

Ұлттық статистика бюросының деректері бойынша, Қазақстан экономикасы өткен жылы 5% өсім көрсетті.

## Негізгі көрсеткіштер

- ЖІӨ өсімі: 5.2%
- Инфляция деңгейі: 8.1%
- Жұмыссыздық деңгейі: 4.8%

Экономика министрлігі биылғы жылы да оң үрдістің жалғасатынын болжап отыр.

## Өсім факторлары

Экономикалық өсімге негізгі үлес қосқан салалар:
1. Өңдеу өнеркәсібі
2. Құрылыс саласы
3. Қызмет көрсету секторы""",
            "excerpt": "Ұлттық статистика бюросы Қазақстан экономикасының өткен жылы 5% өсім көрсеткенін хабарлады.",
            "category": "economics",
            "author": "editor2"
        },
        {
            "title": "Астанада халықаралық спорт жарысы өтеді",
            "content": """# Астана халықаралық марафонға дайындалуда

Мамыр айында Астанада халықаралық марафон өтеді. Жарысқа 50-ден астам елден спортшылар қатысады.

## Жарыс бағдарламасы

Марафон бірнеше қашықтықта өтеді:
- Толық марафон (42.195 км)
- Жарты марафон (21 км)
- 10 км жүгіру
- 5 км жүгіру

## Тіркелу

Қатысушылар ресми сайт арқылы тіркеле алады. Ерте тіркелгендерге жеңілдік жасалады.""",
            "excerpt": "Мамыр айында Астанада 50-ден астам елден спортшылар қатысатын халықаралық марафон өтеді.",
            "category": "sport",
            "author": "editor"
        },
        {
            "title": "Қазақстанда жаңа мәдени орталық ашылды",
            "content": """# Алматыда заманауи мәдени орталық жұмысын бастады

Алматы қаласында жаңа мәдени орталық ашылды. Орталық театр, көрме залдары және музыкалық студияларды қамтиды.

## Орталықтың мүмкіндіктері

- 500 орындық театр залы
- Көрме галереялары
- Музыкалық студиялар
- Шеберханалар

Орталық жас талантарды дамытуға және мәдени өмірді жандандыруға бағытталған.""",
            "excerpt": "Алматыда театр, галереялар және студияларды қамтитын жаңа мәдени орталық ашылды.",
            "category": "culture",
            "author": "editor2"
        },
        {
            "title": "Білім беру жүйесінде жаңа реформалар",
            "content": """# Қазақстанда білім беру жүйесі жаңарады

Білім министрлігі жаңа реформалар пакетін жариялады. Реформалар оқу бағдарламаларын жаңғыртуды және мұғалімдердің біліктілігін арттыруды көздейді.

## Негізгі өзгерістер

1. Оқу бағдарламаларының жаңартылуы
2. Цифрлық технологиялардың енгізілуі
3. Мұғалімдердің қайта даярлауы
4. Инклюзивті білім беруді дамыту

Реформалар кезең-кезеңімен 2026 жылдан бастап енгізіледі.""",
            "excerpt": "Білім министрлігі оқу бағдарламаларын жаңарту және мұғалімдердің біліктілігін арттыру жөніндегі реформаларды жариялады.",
            "category": "society",
            "author": "editor"
        }
    ]
    
    for i, news in enumerate(news_data):
        category = categories.get(news["category"])
        author = users.get(news["author"])
        
        existing = db.query(Content).filter(Content.title == news["title"]).first()
        if not existing:
            content = Content(
                title=news["title"],
                slug=f"news-{i+1}",
                content=news["content"],
                excerpt=news["excerpt"],
                type=ContentType.NEWS,
                status=ContentStatus.PUBLISHED,
                category_id=category.id if category else None,
                author_id=author.id if author else 1,
                published_at=datetime.now(timezone.utc) - timedelta(days=i),
                view_count=100 + (i * 50)
            )
            db.add(content)
            print(f"✓ Created news: {news['title']}")
    
    db.commit()


def create_sample_articles(db: Session, users: dict[str, User], categories: dict[str, Category]) -> None:
    """Create sample articles."""
    
    articles_data = [
        {
            "title": "Қазақстандағы цифрлық трансформация: мүмкіндіктер мен қиындықтар",
            "content": """# Цифрлық трансформация: Қазақстанның болашағы

Қазақстан соңғы жылдары цифрлық трансформацияға үлкен көңіл бөлуде. Бұл мақалада біз осы процестің негізгі аспектілерін қарастырамыз.

## Қазіргі жағдай

Қазақстан цифрлық дамуда белсенді қадамдар жасауда:
- Электрондық үкімет қызметтерінің дамуы
- Цифрлық инфрақұрылымның жаңартылуы
- IT-білім берудің кеңеюі

## Негізгі мүмкіндіктер

### 1. Электрондық үкімет
Мемлекеттік қызметтердің 80%-дан астамы онлайн режимінде қолжетімді.

### 2. Цифрлық экономика
Цифрлық экономиканың үлесі ЖІӨ-де үнемі өсуде.

### 3. Білім беру
IT-мамандарды даярлау бағдарламалары кеңейтілуде.

## Қиындықтар

Дегенмен, бірқатар қиындықтар да бар:
- Аймақтар арасындағы цифрлық алшақтық
- Кибер қауіпсіздік мәселелері
- Білікті кадрлардың жетіспеушілігі

## Қорытынды

Цифрлық трансформация - бұл ұзақ мерзімді процесс. Табысқа жету үшін мемлекет, бизнес және қоғам бірлесіп жұмыс істеуі керек.""",
            "excerpt": "Қазақстандағы цифрлық трансформация процесінің мүмкіндіктері мен қиындықтарын талдау.",
            "category": "technology",
            "author": "editor"
        },
        {
            "title": "Қазақстан экономикасының әртараптандырылуы: жаңа бағыттар",
            "content": """# Экономиканы әртараптандыру стратегиясы

Қазақстан экономикасын әртараптандыру - ұлттық дамудың басты басымдығы.

## Неліктен әртараптандыру қажет?

Мұнай-газ секторына тәуелділікті азайту үшін:
- Өңдеу өнеркәсібін дамыту
- Ауыл шаруашылығын жаңғырту
- Қызмет көрсету секторын кеңейту

## Басым салалар

### Өңдеу өнеркәсібі
Металлургия, химия өнеркәсібі және машина жасау дамытылуда.

### Агроөнеркәсіп
Экспортқа бағытталған ауыл шаруашылығы өнімдерін өндіру.

### Туризм
Туристік инфрақұрылымды дамыту және халықаралық туристерді тарту.

## Мемлекеттік қолдау

Үкімет әртараптандыруды қолдау үшін:
- Салық жеңілдіктері
- Қаржылық қолдау бағдарламалары
- Инфрақұрылымды дамыту

## Болжам

Сарапшылар 2030 жылға қарай мұнай-газ секторының үлесінің 30%-ға дейін азаюын болжайды.""",
            "excerpt": "Қазақстан экономикасын әртараптандыру стратегиясы және оның іске асыру жолдары.",
            "category": "economics",
            "author": "editor2"
        },
        {
            "title": "Қазақстандағы қоғамдық өзгерістер: жаңа буын",
            "content": """# Жаңа буын: Қазақстандағы әлеуметтік өзгерістер

Қазақстан қоғамы соңғы онжылдықта айтарлықтай өзгерістерге ұшырады.

## Демографиялық өзгерістер

- Жас буынның үлесі артуда
- Урбанизация процесі жалғасуда
- Білім деңгейі жоғарылауда

## Құндылықтардың өзгеруі

### Жаңа буынның басымдықтары:
1. Білім мен кәсіби даму
2. Өзін-өзі іске асыру
3. Экологиялық сана
4. Әлеуметтік белсенділік

## Цифрлық қоғам

Интернет пен әлеуметтік желілер қоғамдық өмірде маңызды рөл атқарады:
- Ақпаратқа қолжетімділік
- Онлайн білім беру
- Электрондық коммерция

## Қиындықтар

- Ұрпақтар арасындағы алшақтық
- Дәстүрлі және заманауи құндылықтардың қақтығысы
- Әлеуметтік теңсіздік

## Болашаққа көзқарас

Қазақстан қоғамы дамудың жаңа кезеңіне қадам басуда.""",
            "excerpt": "Қазақстандағы әлеуметтік өзгерістер және жаңа буынның құндылықтары туралы талдау.",
            "category": "society",
            "author": "editor"
        }
    ]
    
    for i, article in enumerate(articles_data):
        category = categories.get(article["category"])
        author = users.get(article["author"])
        
        existing = db.query(Content).filter(Content.title == article["title"]).first()
        if not existing:
            content = Content(
                title=article["title"],
                slug=f"article-{i+1}",
                content=article["content"],
                excerpt=article["excerpt"],
                type=ContentType.ARTICLE,
                status=ContentStatus.PUBLISHED,
                category_id=category.id if category else None,
                author_id=author.id if author else 1,
                published_at=datetime.now(timezone.utc) - timedelta(days=i+2),
                view_count=200 + (i * 75)
            )
            db.add(content)
            print(f"✓ Created article: {article['title']}")
    
    db.commit()


def seed_content():
    """Main seeding function."""
    print("Starting content seeding...")
    db = SessionLocal()
    
    try:
        # Get categories
        categories = {
            "politics": db.query(Category).filter(Category.slug == "politics").first(),
            "economics": db.query(Category).filter(Category.slug == "economics").first(),
            "society": db.query(Category).filter(Category.slug == "society").first(),
            "culture": db.query(Category).filter(Category.slug == "culture").first(),
            "sport": db.query(Category).filter(Category.slug == "sport").first(),
            "technology": db.query(Category).filter(Category.slug == "technology").first(),
        }
        
        # Create sample users
        users = create_sample_users(db)
        
        # Create sample news
        create_sample_news(db, users, categories)
        
        # Create sample articles
        create_sample_articles(db, users, categories)
        
        print("\n✓ Content seeding completed successfully!")
        print(f"Total news: {db.query(Content).filter(Content.type == ContentType.NEWS).count()}")
        print(f"Total articles: {db.query(Content).filter(Content.type == ContentType.ARTICLE).count()}")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_content()
