
# TODO for sms
# from rest_framework.response import Response

# def phone_required(view_func):
#     def wrapper(request, *args, **kwargs):
#         if is_phone_required(request.user) and not request.user.userphone.is_verified:
#             return Response({"error": "Phone verification required"}, status=403)
#         return view_func(request, *args, **kwargs)
#     return wrapper