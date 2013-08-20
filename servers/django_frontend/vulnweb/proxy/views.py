import requests
from django.http import HttpResponse


def proxy(request):
    '''
    This is a vulnerable view which takes a URL as parameter, performs a
    GET request to it and then returns that response body as the body of the
    initial request.
    
    http://127.0.0.1:8000/?url=http://httpbin.org/user-agent should return
    the python-requests user agent.
    '''
    url = request.GET['url']
    
    try:
        response = requests.get(url)
        text = response.text
    except Exception, e:
        text = 'HTTP request failed %s' % e
    
    return HttpResponse(text)