import asyncio

import spotify
from spotify import User

client = spotify.Client('someid', 'somesecret')

async def main():
    # User authentication is covered with the OAuth 2 authorization flow
    # https://developer.spotify.com/documentation/general/guides/authorization-guide/

    # The process goes a little like this:
    #  - Produce an OAuth url containing your client_id, what scopes you want access to and a redirect_url
    #  - A user follows this url and spotify asks them for permission to allow the app access
    #  - The user accepts and spotify redirects the user with the redirect_url filling in a `code` and `state` values
    #  - The app makes a POST request to spotify exchanging the code for a authorization token and a refresh token
    #  - The app can now make api requests on behalf of the user with the auth token
    #  - Once the auth token expires the app can refresh it with the refresh token

    # There are two constructors for a authorized User
    #  - User.from_code
    #  - User.from_token

    ## User.from_code

    # Once the app has the code (and the state is checked)
    # the library can handle the second half of the oauth flow,
    # getting the tokens and refreshing them.

    # The redirect_uri is required for further validation on spotifys end

    # REFRESHING: enabling a refreshing session is controlled through a kwarg `refresh` that takes a `bool`

    User.from_code(client, 'somecode', redirect_uri='some://redirect', refresh=False)

    ## User.from_token

    # Once the OAuth flow is complete and the app has the tokens
    # the second constructor can be used for a User

    # REFRESHING: enabling a refreshing session is controlled through a kwarg `refresh`
    # Here a tuple must be provided Tuple[Int, String] where the integer is the amount of seconds
    # untill the token expires and the string is the refresh token provided by spotify

    User.from_token(client, 'sometoken', refresh=(3600, 'somerefreshtoken'))

    # STOP REFRESHING: To stop the refreshing task the programmer can cancel it through `User.refresh.cancel()`
    # `User.refresh` is just a read only property pointing to the running coroutine task, if it's None then there
    # is no task running.

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
