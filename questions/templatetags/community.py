from django import template

from questions.models import Question, Tag

register = template.Library()


@register.inclusion_tag("core/includes/sidebar.html")
def community_sidebar():
    return {"tags": Tag.objects.popular()[:3], "authors": Question.objects.top_authors()[:3]}
