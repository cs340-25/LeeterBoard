const grabAllUsers = `
    query globalRanking($page: Int!) {
        globalRanking(page: $page) {
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

const grabUserInfo = `
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

var usernameList = []; // Stores all users

for(var i = 1; i < 5; i++) {
    fetch("https://leetcode.com/graphql/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            query: grabAllUsers,
            variables: { page: i },
        }),
    })
    .then(response => response.json())
    .then(output => {
        for(const currUser of output.data.globalRanking.rankingNodes) {
            // Grab the username of the player on the leaderboard
            var username = currUser.user.username;
            //console.log(username);
            usernameList.push(username);
    
            // Retrieve the user's profile data based on that username passed as a variable
            // fetch("https://leetcode.com/graphql/", {
            //     method: "POST",
            //     headers: { "Content-Type": "application/json" },
            //     body: JSON.stringify({ 
            //         query: grabUserInfo,
            //         variables: { username: `${username}` },
            //     })
            // })
            // .then(response => response.json())
            // .then(output => {
            //     console.log(output.data);
            // })
        }
    })
    .then(() => {
        for(const username of usernameList) {
            //console.log(username);
            
            // Retrieve the user's profile data based on that username passed as a variable
            fetch("https://leetcode.com/graphql/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    query: grabUserInfo,
                    variables: { username: `${username}` },
                }),
            })
            .then(response => response.json())
            .then(output => console.log(output.data));
        }
    });
}