# cr-decks-api
Version 1 of API that uses Python Flask and Firebase to retrieve data from Clash Royale's API (developer.clashroyale.com) and refactors the data to show the real-time player rankings with their deck information.

## Tools
Python Flask, Google Firebase

## Details
Second iteration of Clash Royale Deck Suggestions project after realizing the inefficiencies and privacy issues (i.e., storing API key in .env) of first project. Current iteration requests and formats data and stores that data in Firebase to reduce the total amount of API calls. However, the project had to be terminated due to hitting the rate limit too often and getting IP-banned (refreshing database takes a total of 101 API calls with minimal delays). 

## Next steps
1. Figure out how to not hit the rate limit - instead of fully refreshing the database each time, only update the ones that need updating. 
2. Develop front end for interacting with this API and set restrictions so that other users can't access the API and hit the rate limit.
