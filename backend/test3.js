// QUERY - Get all users from Leetcode Global Leaderboard
const queryAllUsers = `
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

const fetchAllUsers = async () => {
    const allUsers = [];
    for(var i = 1; i <= 5; i++) {
        const response = await fetch('https://leetcode.com/graphql/', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: queryAllUsers,
                variables: { page: i }
            }),
        });

        // response.ok checks success codes from 200-299
        if(!response.ok) {
            throw new Error('Could not fetch users');
        }

        // We now need to go pull the usernames from each page that we want
        const pageInfo = await response.json();
        for(const currUser of pageInfo.data.globalRanking.rankingNodes) {
            allUsers.push(currUser.user.username);
        }
    }

    // gets passed in as 'allUsers' in the promise chain
    return allUsers;
}




const queryUserProfileInfo = `
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

const fetchUserData = async (allUsers) => {
    const userData = [];

    // Loop through all users in the allUsers array
    for(const currUsername of allUsers) {
        const response = await fetch('https://leetcode.com/graphql/', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: queryUserProfileInfo,
                variables: { "username": `${currUsername}` },
            }),
        });

        // validate response
        if(!response.ok) {
            throw new Error('Could not fetch user profile data');
        }

        const profileInfo = await response.json();
        userData.push(profileInfo.data.matchedUser.profile.ranking);
    }

    // gets passed into promise chain as 'userData'
    return userData;
}

fetchAllUsers()
    .then(allUsers => fetchUserData(allUsers))
    .then(userData => console.log(userData));
