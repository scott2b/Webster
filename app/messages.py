"""
Simple session messages implementation. Requires that the request object
have a session. For most frameworks, this will be a dictionary-like session
set on the request object in session middleware.

Usage:

  * call add_message to add a session message to be displayed to the user

  * call clear_messages in the template after rendering out the current session
    messages
"""


def clear_messages(request):
    """Call from a template after rendering messages to clear out the current
    message list.
    """
    request.session['messages']= []
    return ''


def add_message(request, message):
    """Add a message to the session messages list."""
    if not 'messages' in request.session:
        request.session['messages'] = []
    request.session['messages'].append(message)
