import json
import random
import os

random.seed(42)

ANDROID_JOB_TITLES = [
    "Android Developer", "Senior Android Engineer", "Android Software Engineer",
    "Mobile Application Developer", "Senior Mobile Developer", "Android Tech Lead",
    "Android Architect", "Staff Android Engineer", "Android SDK Developer",
    "Principal Mobile Engineer",
]

COMPANIES = [
    "Gojek", "Tokopedia", "Traveloka", "Bukalapak", "Shopee Indonesia",
    "Grab Indonesia", "Bank Mandiri", "BCA", "BNI", "Bank BRI",
    "OVO", "Dana", "Gopay", "LinkAja", "Jenius",
    "Blibli", "Sociolla", "Zalora Indonesia", "EcommerceID", "Ralali",
    "Kredivo", "Akulaku", "SeaBank", "Bank Jenius", "Bank Jago",
    "Astra Financial", "Home Credit Indonesia", "Klinik Pintar", "Halodoc",
    "Alodokter", "ProSehat", "SehatQ", "GrabHealth", "GoMed",
    "Ruangguru", "Zenius", "Cakap", "Quipper", "HarukaEdu",
    "Binar Academy", "Dicoding", "Skill Academy", "Pahamify", "CoLearn",
    "Kumparan", "IDN Media", "Detik Network", "Bola Net", "Viva Media Asia",
    "MNC Media", "KG Media", "SCTV", "RCTI+", "Vidio",
    "Sayurbox", "TaniHub", "Efishery", "Kedai Sayur", "Warung Pintar",
    "PaDi UMKM", "Bibit", "Bareksa", "Stockbit", "Ajaib",
    "Pintek", "Danamas", "Modal Rakyat", "Investree", "Amartha",
    "Ninja Van Indonesia", "JNE", "J&T Express", "Sicepat", "Anteraja",
    "Lion Parcel", "Waresix", "Kargo", "Ritase", "Logisly",
    "Accenture Indonesia", "Microsoft Indonesia", "Google Indonesia", "Apple Developer Academy",
    "ShopBack Indonesia", "Tiket.com", "Airy Rooms", "RedDoorz", "OYO Indonesia",
    "Mekari", "Talenta", "Jurnal", "Sleekr", "Kitalulus",
    "Travelio", "Mamikos", "Rukita", "Pinhome", "Rumah.com",
    "GovTech Edu", "Digital Government", "BPJS Kesehatan", "Kemendikbud", "Bappenas",
]

TECH_KEYWORDS = [
    "Kotlin", "Java", "Jetpack Compose", "Clean Architecture",
    "MVVM", "MVI", "Coroutines", "Flow", "Hilt", "Koin", "Dagger",
    "Retrofit", "OkHttp", "REST API", "GraphQL", "WebSocket",
    "Room DB", "DataStore", "SQLite", "Firebase", "Crashlytics",
    "JUnit", "MockK", "Espresso", "GitHub Actions", "Fastlane",
    "Google Play Console", "Material Design 3", "Adaptive Layout",
    "ML Kit", "CameraX", "TFLite", "LiteRT", "ONNX",
    "WorkManager", "Navigation Component", "Paging 3",
    "NDK", "JNI", "llama.cpp", "whisper.cpp",
    "CI/CD", "RESTful API", "Agile", "Scrum", "Git",
    "Performance Optimization", "Code Review", "Unit Testing",
    "Firebase Auth", "Firestore", "Cloud Messaging",
    "Jetpack Libraries", "Android SDK", "Google Maps",
    "On-Device AI", "Machine Learning", "LLM Inference",
    "StateFlow", "SharedFlow", "Reactive Programming",
    "Modular Architecture", "Offline-First", "Encryption",
    "Play Store", "App Distribution",
]

SKILL_AREAS = [
    ("Jetpack Compose Migration", "experience migrating production apps from XML to Jetpack Compose"),
    ("Modular Architecture", "designed and implemented modular Android architecture with dynamic feature modules"),
    ("Performance Optimization", "optimized app performance including startup time, memory usage, and rendering"),
    ("CI/CD Pipeline", "built and maintained CI/CD pipelines for automated testing and deployment"),
    ("Payment Integration", "integrated payment gateways including Midtrans, Xendit, and GoPay"),
    ("On-Device AI Inference", "integrated on-device LLM inference using llama.cpp and whisper.cpp via JNI/NDK bridge"),
    ("Offline-First Architecture", "designed offline-first architecture with Room, WorkManager, and local AI model orchestration"),
    ("Security & Encryption", "implemented encryption, secure storage, biometric auth, and certificate pinning"),
    ("Firebase Suite", "integrated Firebase Auth, Firestore, Cloud Messaging, Analytics, and Crashlytics"),
    ("Mobile Machine Learning", "deployed custom CNN and vision-language models on-device with LiteRT and ONNX runtime"),
]

LOCATIONS = [
    "Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Bali",
    "Remote, Indonesia", "Hybrid - Jakarta", "Remote",
]

SENIORITY_LEVELS = ["Junior", "Mid-Level", "Senior", "Staff", "Lead"]

RESPONSIBILITIES_POOL = [
    "Design and implement new features for Android applications with clean architecture",
    "Collaborate with product managers, designers, and backend engineers to deliver user-centric solutions",
    "Write unit tests, integration tests, and UI tests to ensure code quality",
    "Conduct code reviews and mentor junior developers on best practices",
    "Optimize application performance, memory usage, and network efficiency",
    "Participate in sprint planning, daily standups, and retrospective ceremonies",
    "Contribute to architecture decisions and technical roadmaps",
    "Manage Google Play Store releases including staged rollouts and A/B testing",
    "Integrate third-party SDKs and RESTful APIs",
    "Troubleshoot production issues and implement hotfixes",
    "Create and maintain technical documentation",
    "Continuously research and adopt new Android technologies and best practices",
    "Implement Material Design guidelines for intuitive user interfaces",
    "Collaborate on API contract design with backend teams",
    "Ensure app compliance with security standards and data privacy regulations",
    "Build reusable components and libraries for cross-project use",
    "Set up and maintain CI/CD pipelines with automated build and test workflows",
    "Work on accessibility features to make apps inclusive for all users",
    "Implement analytics and crash reporting to drive data-informed decisions",
    "Lead technical discovery and proof-of-concept development for new features",
]

REQUIREMENTS_POOL = [
    "Bachelor's degree in Computer Science or related field",
    "X+ years of professional Android development experience",
    "Strong proficiency in Kotlin and Java",
    "Experience with Jetpack Compose and modern Android UI development",
    "Deep understanding of Clean Architecture, MVVM, and SOLID principles",
    "Experience with dependency injection (Hilt/Koin/Dagger)",
    "Proficiency with Coroutines and Flow for asynchronous programming",
    "Experience with Room database and local data persistence",
    "Familiarity with Firebase services (Auth, Firestore, Messaging, Analytics)",
    "Experience with CI/CD tools (GitHub Actions, Fastlane)",
    "Strong knowledge of RESTful API integration with Retrofit/OkHttp",
    "Experience with version control systems (Git)",
    "Understanding of Material Design guidelines and accessibility",
    "Experience with unit testing frameworks (JUnit, MockK, Espresso)",
    "Excellent problem-solving and communication skills",
    "Experience with Google Play Console and app release management",
    "Knowledge of performance optimization tools (Profiler, LeakCanary, etc.)",
    "Familiarity with Agile/Scrum development methodologies",
    "Experience with modular architecture and multi-module projects",
    "Knowledge of security best practices for mobile applications",
    "Experience with JNI/NDK integration for native C/C++ libraries",
    "Hands-on experience with on-device ML inference (TFLite, ONNX, llama.cpp)",
    "Experience deploying machine learning models on mobile devices",
    "Strong understanding of Android NDK and native development",
    "Experience with LLM integration and prompt engineering on mobile",
    "Familiarity with GPU-accelerated inference (Vulkan, OpenCL)",
    "Knowledge of audio processing and speech-to-text pipelines",
    "Experience with WebSocket and real-time communication protocols",
    "Background in fintech, banking, or payment systems integration",
    "Published Android applications on Google Play Store",
]

NICE_TO_HAVE_POOL = [
    "Experience with GraphQL and Apollo Android",
    "Knowledge of Flutter or React Native",
    "Contributions to open-source Android projects",
    "Published apps on Google Play Store",
    "Experience with machine learning and ML Kit",
    "Knowledge of CI/CD tools like Fastlane",
    "Experience with Kotlin Multiplatform",
    "Published technical blog posts or speaking at conferences",
    "Experience with advanced animations and transitions in Compose",
    "Knowledge of Android automotive or wearable development",
    "Google Associate Android Developer certification",
    "Experience with WebSocket and real-time communication",
    "Background in fintech, banking, or payment systems",
    "Familiarity with Jetpack Navigation and Paging 3",
    "Experience with test-driven development (TDD)",
]


CORE_REQUIREMENTS = [
    "Strong proficiency in Kotlin and Java",
    "Experience with Jetpack Compose and modern Android UI development",
    "Deep understanding of Clean Architecture, MVVM, and SOLID principles",
    "Experience with dependency injection (Hilt/Koin/Dagger)",
    "Proficiency with Coroutines and Flow for asynchronous programming",
    "Experience with Room database and local data persistence",
    "Familiarity with Firebase services (Auth, Firestore, Messaging, Analytics)",
    "Experience with CI/CD tools (GitHub Actions, Fastlane)",
    "Strong knowledge of RESTful API integration with Retrofit/OkHttp",
    "Experience with version control systems (Git)",
    "Understanding of Material Design guidelines and accessibility",
    "Experience with unit testing frameworks (JUnit, MockK, Espresso)",
    "Excellent problem-solving and communication skills",
    "Experience with Google Play Console and app release management",
    "Familiarity with Agile/Scrum development methodologies",
]

CORE_TECH_STACK = [
    "Kotlin", "Java", "Jetpack Compose", "Clean Architecture",
    "MVVM", "Coroutines", "Flow", "Hilt", "Retrofit",
    "Room", "Firebase", "Git", "Material Design",
    "REST API", "Unit Testing", "Google Play Console",
]

def generate_job_posting(index: int) -> dict:
    title = random.choice(ANDROID_JOB_TITLES)
    company = random.choice(COMPANIES)
    location = random.choice(LOCATIONS)

    skill_area, skill_desc = random.choice(SKILL_AREAS)

    # Always include some core requirements + random extras
    core_count = random.randint(3, 5)
    extra_count = random.randint(2, 4)
    core_skills = random.sample(CORE_REQUIREMENTS, min(core_count, len(CORE_REQUIREMENTS)))
    extra_skills = random.sample(REQUIREMENTS_POOL, min(extra_count, len(REQUIREMENTS_POOL)))
    required_skills = core_skills + extra_skills

    nice_haves = random.sample(NICE_TO_HAVE_POOL, min(random.randint(1, 3), len(NICE_TO_HAVE_POOL)))

    num_responsibilities = random.randint(4, 7)
    responsibilities = random.sample(RESPONSIBILITIES_POOL, min(num_responsibilities, len(RESPONSIBILITIES_POOL)))

    # Core tech stack + extra random tech
    core_tech_count = random.randint(4, 6)
    extra_tech_count = random.randint(2, 5)
    core_tech = random.sample(CORE_TECH_STACK, min(core_tech_count, len(CORE_TECH_STACK)))
    extra_tech = random.sample(TECH_KEYWORDS, min(extra_tech_count, len(TECH_KEYWORDS)))
    tech_stack = core_tech + extra_tech

    min_exp = random.choice([2, 3, 4, 5, 6, 7])
    max_exp = min_exp + random.choice([1, 2, 3])

    salary_min = random.choice([8, 10, 12, 15, 18, 20, 25]) * 1_000_000
    salary_max = salary_min + random.choice([5, 7, 10, 15, 20]) * 1_000_000

    return {
        "id": f"JOB-2026-{index:04d}",
        "title": title,
        "company": company,
        "location": location,
        "employment_type": random.choice(["Full-time", "Contract", "Full-time"]),
        "work_setup": random.choice(["On-site", "Remote", "Hybrid", "Remote", "Hybrid"]),
        "salary_range": f"IDR {salary_min:,} - IDR {salary_max:,}",
        "experience_required": f"{min_exp}-{max_exp} years",
        "description": (
            f"We are looking for a talented {title} to join our team at {company}. "
            f"In this role, you will {skill_desc}. "
            f"You will work with a dynamic team to build and maintain high-quality Android applications "
            f"that serve millions of users across Indonesia."
        ),
        "key_responsibilities": responsibilities,
        "required_skills": required_skills,
        "nice_to_have": nice_haves,
        "tech_stack": tech_stack,
        "posted_date": f"2026-{random.randint(1,6):02d}-{random.randint(1,28):02d}",
        "source": random.choice(["LinkedIn", "Karir.com", "Glints", "Jobstreet", "Indeed"]),
    }


def generate_job_postings(count: int = 100) -> list[dict]:
    return [generate_job_posting(i + 1) for i in range(count)]


def export_jobs_to_json(jobs: list[dict], output_path: str):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(jobs, f, indent=2)


if __name__ == "__main__":
    jobs = generate_job_postings(100)
    export_jobs_to_json(jobs, "data/synthetic_jobs.json")
    print(f"Generated {len(jobs)} synthetic Android job postings")
