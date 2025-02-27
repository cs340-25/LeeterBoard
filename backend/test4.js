// GraphQL Query that hits LeetCode's global ranking leaderboard
const queryAllUsers = `
    query globalRanking($page: Int!) {
        globalRanking(page: $page) {
            rankingNodes {
                user {
                    username
                }
            }
        }
    }
`;

// Makes a fetch request for a single page and returns the promise
const fetchAllUsers = async (pageId) => {
    try {
        // The for loop is initializing a bunch of these fetch requests
        // This immediately returns a Promise object, that only resolves into a Response object once its finished
        const response = await fetch("https://leetcode.com/graphql/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: queryAllUsers,
                variables: { page: pageId }
            })
        });
        
        // This line takes the Response from fetch() and transforms it into a JSON Object
        // Each JSON Object for each fetch request gets stored in the responses array
        return await response.json();
    } catch (error) {
        console.error(`Error fetching id: ${pageId}`, error);
        return null;
    }
};

// GraphQL Query that grabs the user profile data (school, avatar)
const queryUserProfileInfo = `
    query userPublicProfile($username: String!) {
        matchedUser(username: $username) {
            username
            profile {
            userAvatar
            school
            }
        }
    }
`;

const fetchUserProfileInfo = async (username) => {
    try {
        const response = await fetch('https://leetcode.com/graphql/', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: queryUserProfileInfo,
                variables: { username: username }
            })
        });

        return await response.json();
    } catch (error) {
        console.error(`Error fetching user: ${username}`, error);
        return null;
    }
}


const main = async () => {
    const globalRequests = [];
    for(let pageId = 1; pageId <= 30; pageId++) {
        // Makes the fetchAllUsers() fetch request for each page
        const globalRequest = fetchAllUsers(pageId);
        // Pushes the immediate Promises from the fetches to the requests array
        globalRequests.push(globalRequest);
    }
    // Makes all requests in parallel and returns a single Promise
    // responses becomes an array of JSON objects
    const globalResponses = await Promise.all(globalRequests);

    // Grabs the username from the array of JSON objects
    const allUsers = (globalResponses).flatMap(res => {
        return res.data.globalRanking.rankingNodes.map(node => node.user.username);
    })

    // We now have an allUsers array of all the users on the site
    // Make fetch requests for each user
    const userProfileRequests = [];
    for(let i = 0; i < allUsers.length; i++) {
        const userProfileRequest = fetchUserProfileInfo(allUsers[i]);
        userProfileRequests.push(userProfileRequest);
    }

    const schools = [];
    const userProfileResponses = await Promise.all(userProfileRequests);
    const allUserProfiles = (userProfileResponses).flatMap(res => {
        var school = res.data.matchedUser.profile.school;
        if(school) {
            console.log(school);
            schools.push(school);
        }
    })
}

main();
