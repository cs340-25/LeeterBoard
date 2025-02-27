const express = require("express");
const app = express();
const PORT = 3000;

app.use(express.static("public"));

app.get("/api/leaderboard", (req, res) => {
    const universities = [
        { name: "University A", avg_rating: 1500, rating_change: 10 },
        { name: "University B", avg_rating: 1480, rating_change: 5 },
    ];
    const trendingUsers = [
        { name: "User1", change: 15 },
        { name: "User2", change: 10 },
    ];
    const trendingUniversities = [
        { name: "University A", change: 20 },
    ];
    const topUniversities = [
        { name: "University A" },
        { name: "University B" },
    ];

    if (req.query.university) {
        return res.json({
            students: [
                { username: "Student1", rating: 1600, rating_change: 12 },
                { username: "Student2", rating: 1580, rating_change: -3 },
            ],
        });
    }

    res.json({ universities, trendingUsers, trendingUniversities, topUniversities });
});

app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));

