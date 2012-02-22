# -*- encoding: utf-8 -*-
import urllib
import urllib2
import json
import base64


class GumroadLink(object):
    id=""
    name=""
    description=""
    price=0
    currency=""
    short_url=""

    def __init__(self, params):
        """"""
        self.__dict__.update(params)
    
    def set_prefix_currency(self):
        raise AttributeError("read only")
    def get_prefix_currency(self):
        if self.currency == "usd":
            return "$"
        elif self.currency == "yen":
            return "\\"
        else:
            return self.currency
    prefix_currency = property(get_prefix_currency, set_prefix_currency)

    def set_suffix_currency(self):
        raise AttributeError("read only")
    def get_suffix_currency(self):
        if self.currency == "usd":
            return "cents"
        elif self.currency == "yen":
            return u"円"
        else:
            return ""
    suffix_currency = property(get_suffix_currency, set_suffix_currency)
            
    def __repr__(self):
        return "< GumLink: {name} ({prefix} {price} {suffix}) >".format(
                name=self.name,
                prefix=self.prefix_currency,
                price=str(self.price),
                suffix=self.suffix_currency
                )


class GumroadClient(object):
    END_POINT = "https://gumroad.com/api/v1"
    TIMEOUT = 10
    token = None
    endpoint = None

    def required_auth(f):
        def wrap(self, *args, **kwargs):
            if not self.token:
                raise Exception("required authentication")
            return f(self, *args, **kwargs)
        return wrap

    def __init__(self, token=None):
        self.endpoint = self.END_POINT
        if token:
            self.token = token
        self._install_opener()
        
    def _install_opener(self):
        opener = urllib2.build_opener(urllib2.HTTPSHandler())
        urllib2.install_opener(opener)
        
    def _build_endpoint(self, call):
        return self.endpoint + "/" + call
    
    def _get_authenticate_url(self):
        return self._build_endpoint("sessions")
   
    def _get_deauthenticate_url(self):
        return self._get_authenticate_url()
    
    def _get_link_url(self, id=None):
        url = self._build_endpoint("links")
        if id:
            url += "/" + str(id)
        return url

    def _encode_params(self, params):
        if not params:
            return None
        for k, v in params.iteritems():
            if hasattr(v, "encode"):
                params[k] = v.encode("utf-8")
        
        return urllib.urlencode(params)

    def _request(self, method, url, params=None):
        params_encoded = self._encode_params(params)
        
        if method == "GET":
            if params_encoded:
                url = url + "?" + params_encoded
            req = urllib2.Request(url)
        else:
            #req = urllib2.Request(url, data=params_encoded)
            req = urllib2.Request(url)
            req.add_data(params_encoded)
            
        if method in ("PUT", "DELETE"):
            req.get_method = lambda: method
        
        if self.token:
            base64string = \
                base64.encodestring("{token}:".format(token=self.token)).strip()
            req.add_header("Authorization", "Basic %s" % base64string)   

        try:
            result = urllib2.urlopen(req, timeout=self.TIMEOUT).read()
        except urllib2.HTTPError, e:
            if e.code in (400, 401, 402, 404, 500, 502, 503, 504):
                result = e.read()
            else:
                raise Exception(
                        "code={code}, url={url}, error={error}".format(
                            code=e.code,
                            url=url,
                            error=e))
        except urllib2.URLError, e:
            raise Exception(
                    "url={url}, error={error}".format(
                        url=url,
                        error=e))

        response = json.loads(result)
        if not response["success"]:
            message = "Unknown error"
            if response.has_key("error") and response["error"].has_key("message"):
                message = response["error"]["message"]
            elif response.has_key("message"):
                message = response["message"]
            raise Exception(message)

        return response

    def authenticate(self, email, password):
        url = self._get_authenticate_url()
        params = dict(email=email, password=password)
        response = self._request("POST", url, params)
        self.token = response["token"]
        return self
        
    @required_auth
    def deauthenticate(self):
        url = self._get_deauthenticate_url()
        response = self._request("DELETE", url)
        self.token = None
        return self
    
    @required_auth
    def add_link(self, name, linkurl, price, description):
        posturl = self._get_link_url()
        params = dict(name=name, url=linkurl, price=price, description=description)
        response = self._request("POST", posturl, params)
        return GumroadLink(response["link"])

    @required_auth
    def get_link(self, id):
        url = self._get_link_url(id)
        response = self._request("GET", url)
        return GumroadLink(response["link"])
        
    @required_auth
    def edit_link(self, link):
        url = self._get_link_url(link.id)
        params = dict(name=link.name, url=link.url, price=link.price,
                      description=link.description)
        response = self._request("PUT", url, params)
        return GumroadLink(response["link"])
    
    @required_auth
    def delete_link(self, link):
        url = self._get_link_url(link.id)
        response = self._request("DELETE", url)
        return self
        
    @required_auth
    def get_links(self):
        url = self._get_link_url()
        response = self._request("GET", url)
        links = []
        if response["links"].count > 0:
            links = [ GumroadLink(link) for link in response["links"] ]
        return links


