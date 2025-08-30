from flask import request

def paginate_query(query, default_limit=10, max_limit=50):
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", default_limit))
        if limit > max_limit:
            limit = max_limit
    except:
        page, limit = 1, default_limit

    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, page, limit
