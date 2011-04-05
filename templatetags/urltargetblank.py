from google.appengine.ext import webapp

register = webapp.template.create_template_register()

@register.filter
def url_target_blank(text):
    return text.replace('<a ', '<a target="_blank" ')