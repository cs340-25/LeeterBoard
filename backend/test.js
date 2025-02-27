/*

Need to pull:
-User information from global leaderboard
-Schools of all those users

*/


// Grab user information from global leaderboard
const queryOne = `
    query globalRanking {
    globalRanking(page: 1) {
        totalUsers
        rankingNodes {
        currentRating
        dataRegion
        user {
            username
            profile {
            userAvatar
            countryName
            }
        }
        }
    }
    }
`;

fetch("https://leetcode.com/graphql/", { // Fetch is returning a Promise that resolves to a Response object
    method: "POST",
    headers: { "Content-Type": "application/json"},
    body: JSON.stringify({ query: queryOne })
})
.then(response => response.json()) //  Converts the Response Promise to JSON
.then(output => { // Uses the Parsed JSON data
    for(const curr of output.data.globalRanking.rankingNodes) {
        console.log(curr);
    }
});



// Grab user information from profile
// Going to need this for pulling avatar, school, etc
const queryTwo = `
    query userPublicProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
            ranking
            userAvatar
            school
            countryName
            skillTags

            }
        }
    }
`;

fetch("https://leetcode.com/graphql/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
        query: queryTwo,
        variables: { username: "coleprice" },
    }),
})
.then(response => response.json())
.then(output => console.log(output.data));



// Grab contest information from user profile
// Important for contest ratings
const queryThree = `
    query userContestRankingInfo($username: String!) {
    userContestRanking(username: $username) {
        rating
    }
    userContestRankingHistory(username: $username) {
        trendDirection
        rating
        ranking
    }
    }
`;

fetch("https://leetcode.com/graphql/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        query: queryThree,
        variables: { username: "coleprice" },
    }),
})
.then(response => response.json())
.then(output => {
    console.log(output.data.userContestRanking);

    var size = output.data.userContestRankingHistory.length; 
    var secondLastElement = output.data.userContestRankingHistory[size - 2];
    console.log(secondLastElement);
});


