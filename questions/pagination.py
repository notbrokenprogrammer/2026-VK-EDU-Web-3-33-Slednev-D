from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    try:
        page = paginator.page(request.GET.get("page", 1))
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)
    page.visible_numbers = paginator.get_elided_page_range(page.number)
    return page
