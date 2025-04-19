const trendingQuizzes = [
    { icon: "🧮", title: "Maths", link: "maths.html" },
    { icon: "🔬", title: "EVS", link: "evs.html" },
    { icon: "🧠", title: "General Knowledge", link: "gk.html" },
    { icon: "🌍", title: "Social Studies", link: "social.html" },
    { icon: "✒️", title: "English Literature", link: "literature.html" },
    { icon: "📚", title: "English Grammar", link: "grammar.html" },
    { icon: "🏀", title: "Sports Trivia", link: "sports.html" }
];

    let currentPosition = 0;
    const cardWidth = 216;
    const scrollContainer = document.getElementById('trendingScroll');

    function createQuizCard(quiz) {
        return `
            <div class="quiz-card">
                <div class="quiz-icon">${quiz.icon}</div>
                <div class="quiz-title">${quiz.title}</div>
                
            </div>
        `;
    }

    function initializeTrendingQuizzes() {
        // Create infinite effect by duplicating items
        const quizCards = [...trendingQuizzes, ...trendingQuizzes]
            .map(quiz => createQuizCard(quiz))
            .join('');
        scrollContainer.innerHTML = quizCards;
    }

    function slideQuizzes(direction) {
        const maxScroll = -(trendingQuizzes.length * cardWidth);
        
        if (direction === 'right') {
            currentPosition -= cardWidth;
            if (currentPosition < maxScroll) {
                currentPosition = 0;
            }
        } else {
            currentPosition += cardWidth;
            if (currentPosition > 0) {
                currentPosition = maxScroll + cardWidth;
            }
        }
        
        scrollContainer.style.transform = `translateX(${currentPosition}px)`;
    }

    function startAutoScroll() {
        setInterval(() => slideQuizzes('right'), 2000);
    }
