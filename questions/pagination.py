from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    try:
        return paginator.page(request.GET.get("page", 1))
    except (PageNotAnInteger, EmptyPage):
        return paginator.page(1)
