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
    const promises = []
    for(var i = 1; i <= 50; i++) {
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

        // Add to our array of promises
        promises.push(response);
    }

    const res = await Promise.all(promises);

    console.log(promises.length);
}

fetchAllUsers();


// const queryUserProfileInfo = `
//     query userPublicProfile($username: String!) {
//         matchedUser(username: $username) {
//             username
//             profile {
//             ranking
//             userAvatar
//             school
//             countryName
//             skillTags
//             }
//         }
//     }
// `;

// const fetchUserData = async (allUsers) => {
//     const userData = [];

//     // Loop through all users in the allUsers array
//     for(const currUsername of allUsers) {
//         const response = await fetch('https://leetcode.com/graphql/', {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({
//                 query: queryUserProfileInfo,
//                 variables: { "username": `${currUsername}` },
//             }),
//         });

//         // validate response
//         if(!response.ok) {
//             throw new Error('Could not fetch user profile data');
//         }

//         const profileInfo = await response.json();
//         userData.push(profileInfo.data.matchedUser.profile.ranking);
//     }

//     // gets passed into promise chain as 'userData'
//     return userData;
// }

// fetchAllUsers()
//     .then(allUsers => fetchUserData(allUsers))
//     .then(userData => console.log(userData));
