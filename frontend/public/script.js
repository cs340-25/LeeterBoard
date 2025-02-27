document.addEventListener("DOMContentLoaded", () => {
    fetchLeaderboard();
    document.getElementById("search-bar").addEventListener("input", filterByUniversity);
});

async function fetchLeaderboard() {
    const response = await fetch("/api/leaderboard");
    const data = await response.json();

    const leaderboardBody = document.getElementById("leaderboard-body");
    leaderboardBody.innerHTML = "";
    
    data.universities.forEach((uni, index) => {
        const row = `
            <tr>
                <td>${index + 1}</td>
                <td>${uni.name}</td>
                <td>${uni.avg_rating}</td>
                <td>${uni.rating_change > 0 ? "+" : ""}${uni.rating_change}</td>
            </tr>
        `;
        leaderboardBody.innerHTML += row;
    });

    updateSidebar("trending-users-list", data.trendingUsers);
    updateSidebar("trending-universities-list", data.trendingUniversities);
    updateSidebar("top-universities-list", data.topUniversities);
}

function updateSidebar(elementId, list) {
    const ul = document.getElementById(elementId);
    ul.innerHTML = "";
    list.forEach(item => {
        ul.innerHTML += `<li>${item.name} (+${item.change})</li>`;
    });
}

async function filterByUniversity() {
    const searchQuery = document.getElementById("search-bar").value;
    if (searchQuery.length < 2) return fetchLeaderboard();

    const response = await fetch(`/api/leaderboard?university=${searchQuery}`);
    const data = await response.json();
    
    const leaderboardBody = document.getElementById("leaderboard-body");
    leaderboardBody.innerHTML = "";

    data.students.forEach((student, index) => {
        const row = `
            <tr>
                <td>${index + 1}</td>
                <td>${student.username}</td>
                <td>${student.rating}</td>
                <td>${student.rating_change > 0 ? "+" : ""}${student.rating_change}</td>
            </tr>
        `;
        leaderboardBody.innerHTML += row;
    });
}

