from spotify import OAuth2

# spotify.py provides an external OAuth2 object to
# simplify the creation and usage of spotify OAuth2
# Authentication flow.

# Of course if you do not want to create an OAuth2 object
# but simply create an OAuth2 URL you can use OAuth2.url_
#
# OAuth2.url_ has an identical signature to creating
# a regular OAuth2 object, it simply skips creating
# the object and returns a 'valid' url quickly
oauth_url = OAuth2.url_('clientid', 'redirectL//uri')

# the only required arguments are the client_id and the redirect_uri
oauth = OAuth2('clientid', 'redirect://uri')

# requiring scopes is simply instantiating an OAuth2 object
# with `scopes='some-scope another-scope' or if you prefer
# dynamically assigning the scope after the object init
# for instance:
oauth.scope = 'some-scope another-scope'

# A spotify.OAuth2 object has only three properties
# attrs, parameters and url.

print(oauth.attrs)       # A key value dict of the OAuth2 parameters.
print(oauth.parameters)  # A url encoded string of the attrs.
print(oauth.url)         # The auth path with the parameters suffixed.

# It is highly recommended you provide a 
# cryptographically secure state parameter
# (you may also dynamically set the state)
# (additionally see here: https://auth0.com/docs/protocols/oauth2/oauth-state)

oauth.state = 'cryptographically-random-state'

# spotify.OAuth2 also takes in a one time keyword only
# argument on instantiation `secure` this argument
# sets the protocol to be used in the url either
# `http` or `https`. secure defaults to True and when
# secure is not True the protocol will `http` instead
# of `https`
